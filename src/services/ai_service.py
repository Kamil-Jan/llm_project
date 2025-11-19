import json
import pytz
from datetime import datetime
from typing import List, Dict, Any, Tuple

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from openai import OpenAI

from ..config.settings import settings
from ..models import AstroDocument
from ..utils.logger import setup_logger
from .search_service import SearchService
from .service import Service
from .user_settings_service import UserSettingsService

logger = setup_logger(__name__)


class OpenRouterEmbeddings(Embeddings):

    def __init__(self, api_key: str, model: str, base_url: str):
        super().__init__()
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )
        self.model = model

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        response = self.client.embeddings.create(
            model=self.model,
            input=texts,
            encoding_format="float"
        )
        return [item.embedding for item in response.data]

    def embed_query(self, text: str) -> List[float]:
        response = self.client.embeddings.create(
            model=self.model,
            input=[text],
            encoding_format="float"
        )
        return response.data[0].embedding


class AiService(Service):
    def __init__(self, search_service: SearchService, user_settings_service: UserSettingsService):
        super().__init__(logger)
        self.search_service = search_service
        self.user_settings_service = user_settings_service
        self.faiss_index_path = "faiss_index"
        self.vector_store = None
        self.chunk_size = 1000
        self.chunk_overlap = 200
        self.llm_client = OpenAI(
            api_key=settings.openai_api_key,
            base_url="https://openrouter.ai/api/v1"
        )

    async def initialize(self):
        await super().initialize()
        await self.load_faiss_index()

    def _clean_json_response(self, content: str) -> str:
        """
        Очищает ответ LLM от markdown форматирования
        Удаляет ```json и ``` блоки, если они есть
        """
        content = content.strip()

        # Удаляем markdown блоки
        if content.startswith("```json"):
            content = content[7:]  # Убираем ```json
        elif content.startswith("```"):
            content = content[3:]  # Убираем ```

        if content.endswith("```"):
            content = content[:-3]  # Убираем закрывающие ```

        return content.strip()

    async def update_database(self, force: bool = False):
        try:
            is_outdated = await AstroDocument.is_outdated(days=7)

            if not is_outdated and not force:
                self.logger.info("Astro documents are up to date, skipping update")
                return

            self.logger.info("Astro documents are outdated, updating...")

            await AstroDocument.delete_all()
            self.logger.info("Deleted all old documents")

            query = f"Астрологический календарь на неделю {datetime.now().strftime('%d.%m.%Y')}"
            doc_count = 0

            for doc_data in self.search_service.search_docs(
                query=query,
                num_results=5,
                fetch_full_content=True
            ):
                content = doc_data['content']
                await AstroDocument.create(content=content)
                doc_count += 1
                self.logger.info(f"Saved document {doc_count}")

            self.logger.info(f"Successfully updated database with {doc_count} documents")

            if doc_count > 0:
                self.logger.info("Creating FAISS vector store...")
                await self._create_faiss_index()
                self.logger.info("FAISS vector store created successfully")

        except Exception as e:
            self.logger.error(f"Failed to update database: {e}")
            raise


    async def load_faiss_index(self):
        """Загрузка FAISS индекса из файла."""
        import os

        try:
            if not os.path.exists(self.faiss_index_path):
                self.logger.warning(f"FAISS index not found at {self.faiss_index_path}, will create on first update")
                return

            self.logger.info(f"Loading FAISS index from {self.faiss_index_path}")

            embeddings = OpenRouterEmbeddings(
                api_key=settings.openai_api_key,
                model="qwen/qwen3-embedding-8b",
                base_url="https://openrouter.ai/api/v1"
            )

            self.vector_store = FAISS.load_local(
                self.faiss_index_path,
                embeddings,
                allow_dangerous_deserialization=True
            )

            self.logger.info("FAISS index loaded successfully")

        except Exception as e:
            self.logger.error(f"Failed to load FAISS index: {e}")
            self.vector_store = None

    def _split_documents_to_chunks(self, documents: List[Document]) -> List[Document]:
        """Разбиение документов на чанки с перекрытием."""
        self.logger.info(f"Splitting {len(documents)} documents into chunks (size={self.chunk_size}, overlap={self.chunk_overlap})")

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )

        chunks = text_splitter.split_documents(documents)
        self.logger.info(f"Created {len(chunks)} chunks from {len(documents)} documents")

        return chunks

    async def _create_faiss_index(self):
        try:
            documents = await AstroDocument.all().order_by('-created_at')

            if not documents:
                self.logger.warning("No documents found for FAISS indexing")
                return

            self.logger.info(f"Creating FAISS index from {len(documents)} documents")

            langchain_docs = [
                Document(
                    page_content=doc.content,
                    metadata={
                        "doc_id": doc.id,
                        "created_at": str(doc.created_at)
                    }
                )
                for doc in documents
            ]

            chunks = self._split_documents_to_chunks(langchain_docs)

            for i, chunk in enumerate(chunks):
                chunk.metadata["chunk_id"] = i
                chunk.metadata["chunk_index"] = i

            self.logger.info(f"Creating embeddings for {len(chunks)} chunks...")

            embeddings = OpenRouterEmbeddings(
                api_key=settings.openai_api_key,
                model="qwen/qwen3-embedding-8b",
                base_url="https://openrouter.ai/api/v1"
            )

            self.vector_store = FAISS.from_documents(chunks, embeddings)
            self.vector_store.save_local(self.faiss_index_path)

            self.logger.info(f"FAISS index with {len(chunks)} chunks saved to {self.faiss_index_path}")

        except Exception as e:
            self.logger.error(f"Failed to create FAISS index: {e}")
            raise

    def search_similar_chunks(self, query: str, k: int = 5) -> List[Document]:
        if not self.vector_store:
            self.logger.warning("FAISS index not loaded, cannot search")
            return []

        try:
            results = self.vector_store.similarity_search(query, k=k)

            self.logger.info(f"Found {len(results)} similar chunks for query")
            for i, doc in enumerate(results, 1):
                self.logger.debug(
                    f"Result {i}: doc_id={doc.metadata.get('doc_id')}, "
                    f"chunk_id={doc.metadata.get('chunk_id')}"
                )

            return results

        except Exception as e:
            self.logger.error(f"Failed to search in FAISS index: {e}")
            return []

    async def _get_owner_settings_with_timezone(self) -> Tuple["UserSettings", str, pytz.BaseTzInfo]:
        owner_settings = await self.user_settings_service.get_owner_settings()
        timezone_name = owner_settings.timezone or settings.timezone
        timezone = pytz.timezone(timezone_name)
        return owner_settings, timezone_name, timezone

    async def _ai_parse_datetime_and_name(
        self,
        text: str,
        timezone_name: str,
        timezone: pytz.BaseTzInfo
    ) -> Dict[str, Any]:
        """Использование LLM для парсинга даты, времени и названия события."""

        system_prompt = """Ты - ассистент для парсинга дат и времени. Твоя задача - извлекать информацию о событии из текста на естественном языке.

Текущий часовой пояс: {timezone}
Текущее время: {current_time}

Распарси текст и верни JSON объект со следующей структурой:
{{
    "start_datetime": "YYYY-MM-DD HH:MM:SS",  // Дата и время начала в ISO формате
    "end_datetime": "YYYY-MM-DD HH:MM:SS",    // Опционально, только если указан временной диапазон
    "event_name": "Название события",          // Название/заголовок события
    "description": "Описание"                  // Опциональное описание
}}

Правила:
1. Всегда возвращай валидный JSON
2. Используй 24-часовой формат для времени
3. Если конкретное время не указано, используй текущее время
4. Если конкретная дата не указана, используй сегодня
5. Для относительного времени типа "через 2 часа", рассчитывай от текущего времени
6. Для дней недели типа "пятница", используй следующее вхождение
7. Для "следующий понедельник", используй понедельник следующей недели
8. Если указан временной диапазон (например, "с 14 до 16"), устанавливай оба времени
9. Держи названия событий краткими но описательными
10. Если четкое название события не найдено, используй "Без названия"

Примеры:
- "завтра в 15:00 Встреча с командой" → {{"start_datetime": "2024-01-16 15:00:00", "event_name": "Встреча с командой"}}
- "пятница с 14:00 до 16:00 Презентация клиенту" → {{"start_datetime": "2024-01-19 14:00:00", "end_datetime": "2024-01-19 16:00:00", "event_name": "Презентация клиенту"}}
- "через 2 часа Обзор проекта" → {{"start_datetime": "2024-01-15 17:30:00", "event_name": "Обзор проекта"}}
- "следующий понедельник в 10:00 Встреча" → {{"start_datetime": "2024-01-22 10:00:00", "event_name": "Встреча"}}
- "tomorrow 3pm Team Meeting" → {{"start_datetime": "2024-01-16 15:00:00", "event_name": "Team Meeting"}}

Возвращай только JSON объект, ничего больше."""

        current_time = datetime.now(timezone)
        formatted_system_prompt = system_prompt.format(
            timezone=timezone_name,
            current_time=current_time.strftime("%Y-%m-%d %H:%M:%S %Z")
        )

        try:
            response = self.llm_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": formatted_system_prompt},
                    {"role": "user", "content": f"Parse this text: {text}"}
                ],
                temperature=0.1,
                max_tokens=10000
            )

            content = response.choices[0].message.content
            self.logger.info(f"AI response: {content}")

            # Очищаем ответ от markdown форматирования
            cleaned_content = self._clean_json_response(content)
            parsed_data = json.loads(cleaned_content)

            if 'start_datetime' not in parsed_data:
                raise ValueError("AI response missing start_datetime")

            return parsed_data

        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse AI response as JSON: {e}")
            raise ValueError("Invalid AI response format")
        except Exception as e:
            self.logger.error(f"LLM API error: {e}")
            raise ValueError(f"AI parsing failed: {e}")

    def _validate_and_convert_datetime(self, datetime_str: str, timezone: pytz.BaseTzInfo) -> datetime:
        """Валидация и конвертация строки datetime в timezone-aware объект."""
        if not datetime_str or datetime_str.strip() == "":
            self.logger.warning("Empty datetime string, using current time")
            now = datetime.now(timezone)
            return now.astimezone(pytz.UTC)

        try:
            dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))

            if dt.tzinfo is None:
                dt = timezone.localize(dt)

            return dt.astimezone(pytz.UTC)

        except Exception as e:
            self.logger.error(f"Failed to validate datetime '{datetime_str}': {e}")
            raise ValueError(f"Invalid datetime format: {datetime_str}")

    def _parse_reminder_times(self, reminder_str: str) -> List[int]:
        """Парсинг времени напоминаний из строки."""
        from ..utils.helpers import parse_reminder_time

        reminder_times = []
        self.logger.info(f"Reminder string: {reminder_str}")
        if reminder_str is None or len(reminder_str) == 0:
            return [15, 60]

        for time_str in reminder_str.split(','):
            time_str = time_str.strip()
            if time_str:
                try:
                    minutes = parse_reminder_time(time_str)
                    reminder_times.append(minutes)
                except Exception:
                    self.logger.warning(f"Could not parse reminder time: {time_str}")

        return reminder_times

    async def process_event_with_astro_context(self, event_data: dict) -> dict:
        self.logger.info(f"Processing event with astro context: {event_data.get('event_name')}")

        try:
            event_datetime = event_data['event_datetime']
            event_name = event_data['event_name']

            event_date_str = event_datetime.strftime('%d %B %Y')
            search_query = f"Астрологический прогноз на {event_date_str}. Событие: {event_name}"
            self.logger.info(f"Searching astro context with query: {search_query}")

            relevant_chunks = self.search_similar_chunks(search_query, k=5)

            if not relevant_chunks:
                self.logger.warning("No astro context found, returning fallback message")
                event_data['result'] = "OK"
                event_data['message'] = "Астрологический прогноз на этот день не найден"
                return event_data

            context_parts = []
            for i, chunk in enumerate(relevant_chunks, 1):
                context_parts.append(f"[Источник {i}]:\n{chunk.page_content}")
            context = "\n\n".join(context_parts)

            astro_prompt = self._create_astro_analysis_prompt(event_data, context)

            self.logger.info("Requesting astro analysis from LLM...")
            response = self.llm_client.chat.completions.create(
                model="openai/gpt-4o-mini",
                messages=[{"role": "user", "content": astro_prompt}],
                temperature=0.3,
                max_tokens=2000,
            )

            astro_response = response.choices[0].message.content
            self.logger.info(f"Received astro analysis raw: {astro_response}")

            cleaned_response = self._clean_json_response(astro_response)
            self.logger.info(f"Cleaned astro analysis: {cleaned_response}")
            astro_analysis = json.loads(cleaned_response)

            event_data['result'] = astro_analysis.get('result', 'OK')
            event_data['message'] = "🔮 Астрологический совет:\n" + astro_analysis.get('message', "")

            self.logger.info(f"Final event data with astro: {event_data}")
            return event_data

        except Exception as e:
            self.logger.error(f"Failed to process astro context: {e}")
            event_data['result'] = "OK"
            event_data['message'] = "Астрологический прогноз на этот день не найден"
            return event_data


    async def _ai_classify_is_event(self, text: str) -> dict:
        """
        Классифицирует текст: является ли он запросом на создание события.
        Возвращает JSON: { "is_event": true/false, "reason": "..." }
        """
        prompt = f"""
    Ты — помощник, который определяет, содержит ли текст запрос на создание события / встречи / задачи.

    Верни JSON строго в формате:
    {{
        "is_event": true/false,
        "reason": "краткое объяснение"
    }}

    Текст: "{text}"

    Правила:
    - is_event = true, если пользователь хочет назначить встречу, событие, задачу, напоминание.
    - is_event = false, если текст — просто разговор, вопрос, приветствие, мнение и т.п.
    - Если есть даже слабый намёк на “назначить”, “встретиться”, “позвонить”, “записаться”, “через 2 часа ...”, — ставь true.
    - Всегда возвращай валидный JSON.
    """

        try:
            response = self.llm_client.chat.completions.create(
                model="openai/gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                max_tokens=200
            )

            content = response.choices[0].message.content
            cleaned = self._clean_json_response(content)
            data = json.loads(cleaned)
            is_event = bool(data.get("is_event", False))
            self.logger.info(f"Event classification for '{text}': {is_event}")
            return is_event
        except Exception as e:
            self.logger.error(f"Failed to classify text as event/non-event: {e}")
            # В случае ошибки классификации лучше ничего не делать, чем ломать логику
            return False

    def _create_astro_analysis_prompt(self, event_data: dict, astro_context: str) -> str:
        """Создание промпта для астрологического анализа события."""

        event_datetime = event_data['event_datetime']
        event_name = event_data['event_name']
        event_description = event_data.get('description', '')
        timezone_name = event_data.get('timezone', settings.timezone)
        timezone = pytz.timezone(timezone_name)

        # Форматируем дату и время
        local_datetime = event_datetime.astimezone(timezone)
        date_str = local_datetime.strftime('%d %B %Y')
        time_str = local_datetime.strftime('%H:%M')
        weekday_str = local_datetime.strftime('%A')

        prompt = f"""Ты — профессиональный астролог. На основе предоставленного астрологического контекста дай краткий совет о планируемом событии.

ИНФОРМАЦИЯ О СОБЫТИИ:
Название: {event_name}
Дата: {date_str} ({weekday_str})
Время: {time_str}
Описание: {event_description if event_description else 'Не указано'}

АСТРОЛОГИЧЕСКИЙ КОНТЕКСТ:
{astro_context}

ЗАДАЧА:
Проанализируй благоприятность этого времени для запланированного события на основе астрологического контекста.

Твой ответ должен быть:
1. Кратким (2-4 предложения)
2. Конкретным (относиться именно к этому событию и времени)
3. Практичным (давать конкретные рекомендации)
4. Основанным на предоставленном астрологическом контексте
5. Дружелюбным и понятным (избегай сложных астрологических терминов, пиши простым языком)
6. Позитивным и поддерживающим (даже если время не идеально)
7. Если время не подходит, то обязательно предложи другое время или дату

Не повторяй информацию о событии, сразу переходи к астрологическому анализу.

Всегда стремись найти позитивные аспекты и считать время скорее подходящим, если контекст не указывает на явные риски. 


Верни ответ в формате JSON со следующей структурой:
{{
    "result": "OK/BAD",
    "message": "Астрологические рекомендации"
}}
result может быть только OK или BAD, если время подходит, то OK, если нет, то BAD
message может быть пустым

Примеры:
- {{"result": "OK", "message": "Астрологический совет: это хорошее время для этого события"}}
- {{"result": "BAD", "message": "Согласно гороскопу, неделя с 3 по 9 ноября 2025 года для знака Водолей не описана,
    но для знака Скорпион эта неделя — время мудрости и заботы о себе, рекомендуется слушать своё сердце и не усложнять задачи.
    Это может говорить о том, что сейчас не самое благоприятное время для важных встреч, требующих концентрации и принятия решений.
    Напутствие: попробуйте перенести встречу на более благоприятное время, например, на следующую неделю."}}
- {{"result": "OK", "message": "Астрологический совет: Завтрашние транзиты выглядят спокойными — даже если день в целом кажется энергически неровным, в вашей личной конфигурации нет напряжённых аспектов, которые могли бы помешать встрече. Влияние планет скорее нейтральное, так что смело назначайте событие: время обещает пройти устойчиво и без неприятных сюрпризов."}}

"""

        return prompt

    async def parse_event_command(self, command_text: str) -> dict:
        await self.update_database(force=False)

        try:
            self.logger.info(f"Parsing command text with AI: '{command_text}'")

            text = command_text.strip()
            if text.startswith('++event'):
                text = text[7:].strip()

            self.logger.info(f"Text after removing ++event prefix: '{text}'")

            is_event = await self._ai_classify_is_event(text)
            if not is_event:
                self.logger.info("Text is not classified as event, doing nothing")
                return None

            # TODO somewhere here you can fetch owner's birthday and use it to calculate the best time for the event
            owner_settings, timezone_name, timezone = await self._get_owner_settings_with_timezone()

            reminder_times = []
            if '--remind' in text:
                parts = text.split('--remind')
                text = parts[0].strip()
                self.logger.info(f'After split: text="{text}", reminder_str="{parts[1].strip() if len(parts) > 1 else ""}"')
                if len(parts) > 1:
                    reminder_str = parts[1].strip()
                    reminder_times = self._parse_reminder_times(reminder_str)

            if not reminder_times:
                reminder_times = list(owner_settings.default_reminder_times)

            parsed_data = await self._ai_parse_datetime_and_name(text, timezone_name, timezone)

            event_datetime = self._validate_and_convert_datetime(parsed_data.get('start_datetime'), timezone)
            end_datetime = None
            if parsed_data.get('end_datetime'):
                end_datetime = self._validate_and_convert_datetime(parsed_data.get('end_datetime'), timezone)

            event_name = parsed_data.get('event_name', 'Untitled Event')

            event_data = {
                'event_name': event_name,
                'description': parsed_data.get('description', ""),
                'event_datetime': event_datetime,
                'end_datetime': end_datetime,
                'reminder_times': reminder_times,
                'timezone': timezone_name
            }

            logger.info(f"Event data: {event_data}")

            return await self.process_event_with_astro_context(event_data)

        except Exception as e:
            self.logger.error(f"Failed to parse event command with AI: {e}")
            raise
