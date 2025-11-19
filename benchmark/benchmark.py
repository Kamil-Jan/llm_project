#!/usr/bin/env python3
"""
Benchmark for Astrological Event Analysis Agent

This benchmark evaluates the performance of an LLM-based astrological agent
in determining the favorability of specific dates and times for various events.
The evaluation uses a curated dataset with ground truth labels and measures
classification metrics including accuracy, precision, recall, and F1-score.
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Tuple
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from project root
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)


class AstroAgentBenchmark:
    """
    Benchmark suite for evaluating astrological event analysis agent.
    
    This class simulates the production environment by:
    1. Using RAG (Retrieval-Augmented Generation) to fetch astrological context
    2. Applying the same prompt template as the production agent
    3. Measuring classification performance against ground truth labels
    """
    
    def __init__(self, api_key: str, dataset: List[dict] = None):
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1"
        )
        self.results = []
        # Store dataset to simulate RAG knowledge base
        self.knowledge_base = dataset if dataset else []
        
    def _simulate_rag_search(self, event_data: dict) -> str:
        """
        Simulates RAG (Retrieval-Augmented Generation) search for astrological context.
        
        In production, this would:
        1. Query FAISS vector store with event details
        2. Retrieve top-k similar document chunks
        3. Construct context from retrieved documents
        
        For benchmarking, we simulate this by retrieving the pre-defined
        astrological context from our knowledge base.
        
        Args:
            event_data: Dictionary containing event information
            
        Returns:
            Astrological context string for the event
        """
        # Simulate similarity search by finding matching event in knowledge base
        for entry in self.knowledge_base:
            if entry['id'] == event_data.get('id'):
                # Format as retrieved document chunks (similar to production)
                context = f"[Retrieved Context - Source 1]:\n{entry['astro_context']}"
                return context
        
        # Fallback if not found
        return "[Retrieved Context - Source 1]:\nНет доступной астрологической информации для этой даты."
    
    def _clean_json_response(self, content: str) -> str:
        """
        Cleans LLM response from markdown formatting.
        
        Args:
            content: Raw LLM response string
            
        Returns:
            Cleaned JSON string
        """
        content = content.strip()
        
        if content.startswith("```json"):
            content = content[7:]
        elif content.startswith("```"):
            content = content[3:]
        
        if content.endswith("```"):
            content = content[:-3]
        
        return content.strip()
    
    def _create_astro_analysis_prompt(self, event_data: dict, astro_context: str) -> str:
        """Создание промпта для астрологического анализа события (из ai_service.py)"""
        
        event_datetime = datetime.fromisoformat(event_data['event_datetime'])
        event_name = event_data['event_name']
        event_description = event_data.get('description', '')
        
        # Форматируем дату и время
        date_str = event_datetime.strftime('%d %B %Y')
        time_str = event_datetime.strftime('%H:%M')
        weekday_str = event_datetime.strftime('%A')
        
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
    
    def evaluate_sample(self, sample: dict) -> dict:
        """
        Evaluates a single sample from the dataset.
        
        Simulates the production pipeline:
        1. RAG retrieval of astrological context
        2. Prompt construction with retrieved context
        3. LLM inference
        4. Response parsing and validation
        
        Args:
            sample: Test sample containing event data and ground truth label
            
        Returns:
            Evaluation result dictionary with predictions and metadata
        """
        print(f"🔮 Evaluating event #{sample['id']}: {sample['event_name']}...")
        
        try:
            # Step 1: Simulate RAG retrieval (as in production ai_service.py)
            astro_context = self._simulate_rag_search(sample)
            
            # Step 2: Construct prompt with retrieved context
            prompt = self._create_astro_analysis_prompt(sample, astro_context)
            
            # Step 3: LLM inference with production model and parameters
            response = self.client.chat.completions.create(
                model="openai/gpt-4o-mini",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,  # Low temperature for consistent predictions
                max_tokens=10000
            )
            
            content = response.choices[0].message.content
            
            # Step 4: Parse and validate response
            cleaned_content = self._clean_json_response(content)
            prediction = json.loads(cleaned_content)
            
            predicted_result = prediction.get('result', 'UNKNOWN')
            expected_result = sample['expected_result']
            
            # Проверяем корректность
            is_correct = predicted_result == expected_result
            
            result = {
                'id': sample['id'],
                'event_name': sample['event_name'],
                'expected': expected_result,
                'predicted': predicted_result,
                'correct': is_correct,
                'message': prediction.get('message', ''),
                'raw_response': content[:200]  # Сохраняем первые 200 символов для отладки
            }
            
            status = "✅" if is_correct else "❌"
            print(f"  {status} Ожидали: {expected_result}, Получили: {predicted_result}")
            
            return result
            
        except Exception as e:
            print(f"  ⚠️ Ошибка при обработке: {e}")
            return {
                'id': sample['id'],
                'event_name': sample['event_name'],
                'expected': sample['expected_result'],
                'predicted': 'ERROR',
                'correct': False,
                'message': str(e),
                'raw_response': ''
            }
    
    def calculate_metrics(self, results: List[dict]) -> Dict[str, float]:
        """Расчет метрик классификации"""
        
        # Подсчет True Positive, True Negative, False Positive, False Negative
        tp = sum(1 for r in results if r['expected'] == 'OK' and r['predicted'] == 'OK')
        tn = sum(1 for r in results if r['expected'] == 'BAD' and r['predicted'] == 'BAD')
        fp = sum(1 for r in results if r['expected'] == 'BAD' and r['predicted'] == 'OK')
        fn = sum(1 for r in results if r['expected'] == 'OK' and r['predicted'] == 'BAD')
        
        total = len(results)
        errors = sum(1 for r in results if r['predicted'] == 'ERROR')
        
        # Accuracy
        accuracy = (tp + tn) / total if total > 0 else 0
        
        # Precision (из тех, что предсказали OK, сколько правильных)
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        
        # Recall (из всех OK, сколько нашли)
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        
        # F1-Score
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        return {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'total_samples': total,
            'correct_predictions': tp + tn,
            'errors': errors,
            'true_positive': tp,
            'true_negative': tn,
            'false_positive': fp,
            'false_negative': fn
        }
    
    def run_benchmark(self, dataset_path: str) -> Tuple[List[dict], Dict[str, float]]:
        """Запуск бенчмарка на датасете"""
        print(f"📊 Начинаем бенчмарк астрологического агента")
        print(f"📁 Загружаем датасет из: {dataset_path}\n")
        
        # Загружаем датасет
        with open(dataset_path, 'r', encoding='utf-8') as f:
            dataset = json.load(f)
        
        print(f"✨ Загружено {len(dataset)} примеров\n")
        
        # Обрабатываем каждый пример
        results = []
        for i, sample in enumerate(dataset, 1):
            print(f"[{i}/{len(dataset)}]", end=" ")
            result = self.evaluate_sample(sample)
            results.append(result)
            print()
        
        # Считаем метрики
        print("\n" + "="*80)
        print("📈 Расчет метрик...")
        metrics = self.calculate_metrics(results)
        
        return results, metrics
    
    def save_metrics_report(self, metrics: Dict[str, float], results: List[dict], output_path: str):
        """Сохранение отчета с метриками в Markdown"""
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("# 🔮 Отчет по бенчмарку астрологического агента\n\n")
            
            # Общая информация
            f.write(f"**Дата запуска:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**Модель:** OpenAI GPT-4o-mini (через OpenRouter)\n")
            f.write(f"**Всего примеров:** {metrics['total_samples']}\n\n")
            
            # Основные метрики
            f.write("## 📊 Основные метрики\n\n")
            f.write("| Метрика | Значение | Описание |\n")
            f.write("|---------|----------|----------|\n")
            f.write(f"| **Accuracy** | {metrics['accuracy']:.2%} | Доля правильных предсказаний |\n")
            f.write(f"| **Precision** | {metrics['precision']:.2%} | Точность положительных предсказаний (OK) |\n")
            f.write(f"| **Recall** | {metrics['recall']:.2%} | Полнота (какую долю OK событий нашли) |\n")
            f.write(f"| **F1-Score** | {metrics['f1']:.2%} | Гармоническое среднее Precision и Recall |\n\n")
            
            # Детальная статистика
            f.write("## 📈 Детальная статистика\n\n")
            f.write("| Показатель | Количество |\n")
            f.write("|------------|------------|\n")
            f.write(f"| Всего примеров | {metrics['total_samples']} |\n")
            f.write(f"| Правильных предсказаний | {metrics['correct_predictions']} |\n")
            f.write(f"| Ошибочных предсказаний | {metrics['total_samples'] - metrics['correct_predictions'] - metrics['errors']} |\n")
            f.write(f"| Ошибок при обработке | {metrics['errors']} |\n\n")
            
            # Confusion Matrix
            f.write("## 🎯 Матрица ошибок (Confusion Matrix)\n\n")
            f.write("|  | Predicted OK | Predicted BAD |\n")
            f.write("|---|---|---|\n")
            f.write(f"| **Actual OK** | {metrics['true_positive']} (TP) | {metrics['false_negative']} (FN) |\n")
            f.write(f"| **Actual BAD** | {metrics['false_positive']} (FP) | {metrics['true_negative']} (TN) |\n\n")
            
            # Интерпретация метрик
            f.write("## 💡 Интерпретация результатов\n\n")
            
            if metrics['accuracy'] >= 0.8:
                f.write("✨ **Отличный результат!** Модель хорошо справляется с определением благоприятности времени.\n\n")
            elif metrics['accuracy'] >= 0.6:
                f.write("👍 **Хороший результат.** Модель показывает приемлемую точность, но есть куда расти.\n\n")
            else:
                f.write("⚠️ **Требуется улучшение.** Модель часто ошибается в оценке благоприятности.\n\n")
            
            # Анализ типов ошибок
            if metrics['false_positive'] > metrics['false_negative']:
                f.write("- **Склонность к оптимизму:** Модель чаще говорит OK, когда нужно сказать BAD (False Positives).\n")
                f.write("- Это означает, что агент может одобрять неблагоприятное время.\n\n")
            elif metrics['false_negative'] > metrics['false_positive']:
                f.write("- **Склонность к пессимизму:** Модель чаще говорит BAD, когда время благоприятно (False Negatives).\n")
                f.write("- Это означает, что агент может отговаривать от хороших моментов.\n\n")
            else:
                f.write("- **Сбалансированная модель:** Ошибки распределены равномерно.\n\n")
            
            # Примеры ошибок
            f.write("## ❌ Примеры неправильных предсказаний\n\n")
            
            errors = [r for r in results if not r['correct'] and r['predicted'] != 'ERROR']
            
            if errors:
                f.write("### False Positives (сказали OK, а надо было BAD)\n\n")
                fp_errors = [e for e in errors if e['expected'] == 'BAD' and e['predicted'] == 'OK']
                if fp_errors:
                    for err in fp_errors[:5]:  # Показываем первые 5
                        f.write(f"- **{err['event_name']}** (ID: {err['id']})\n")
                        f.write(f"  - Ожидали: {err['expected']}, Получили: {err['predicted']}\n\n")
                else:
                    f.write("_Таких ошибок не обнаружено_\n\n")
                
                f.write("### False Negatives (сказали BAD, а надо было OK)\n\n")
                fn_errors = [e for e in errors if e['expected'] == 'OK' and e['predicted'] == 'BAD']
                if fn_errors:
                    for err in fn_errors[:5]:  # Показываем первые 5
                        f.write(f"- **{err['event_name']}** (ID: {err['id']})\n")
                        f.write(f"  - Ожидали: {err['expected']}, Получили: {err['predicted']}\n\n")
                else:
                    f.write("_Таких ошибок не обнаружено_\n\n")
            else:
                f.write("🎉 **Ошибок не найдено!** Модель правильно предсказала все примеры.\n\n")
            
            # Заключение
            f.write("## 🎭 Заключение\n\n")
            f.write("Этот бенчмарк - шуточный, но показывает реальную способность модели анализировать ")
            f.write("астрологический контекст и давать рекомендации. В реальном применении результаты ")
            f.write("могут отличаться в зависимости от качества и полноты астрологических данных.\n\n")
            
            f.write("_Созвано звездами, проверено кодом_ ✨🔮\n")
        
        print(f"\n💾 Отчет сохранен в: {output_path}")


def main():
    """
    Main entry point for the benchmark execution.
    
    Loads configuration, initializes the benchmark suite, runs evaluation,
    and generates a comprehensive metrics report.
    """
    # Load API key from environment
    api_key = os.getenv('OPENAI_API_KEY')
    
    if not api_key:
        print("❌ Error: OPENAI_API_KEY not found in .env file")
        print("   Please create .env file in project root with OPENAI_API_KEY=your_key")
        return
    
    # Define file paths
    script_dir = Path(__file__).parent
    dataset_path = script_dir / 'dataset.json'
    output_path = script_dir / 'metrics.md'
    
    # Validate dataset exists
    if not dataset_path.exists():
        print(f"❌ Error: Dataset not found at {dataset_path}")
        return
    
    # Load dataset for RAG knowledge base simulation
    print(f"📁 Loading dataset from: {dataset_path}")
    with open(dataset_path, 'r', encoding='utf-8') as f:
        dataset = json.load(f)
    
    # Initialize benchmark with dataset (for RAG simulation)
    benchmark = AstroAgentBenchmark(api_key, dataset=dataset)
    results, metrics = benchmark.run_benchmark(str(dataset_path))
    
    # Сохраняем отчет
    benchmark.save_metrics_report(metrics, results, str(output_path))
    
    # Выводим итоговые метрики в консоль
    print("\n" + "="*80)
    print("🎯 ИТОГОВЫЕ МЕТРИКИ:")
    print("="*80)
    print(f"Accuracy:  {metrics['accuracy']:.2%}")
    print(f"Precision: {metrics['precision']:.2%}")
    print(f"Recall:    {metrics['recall']:.2%}")
    print(f"F1-Score:  {metrics['f1']:.2%}")
    print("="*80)
    print(f"\n✅ Бенчмарк завершен! Проверьте {output_path} для подробного отчета.")


if __name__ == "__main__":
    main()

