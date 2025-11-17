import os
import pytz
from datetime import datetime
from typing import Optional, List
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from ..utils.logger import setup_logger
from ..config.settings import settings
from ..models import Event
from .service import Service

logger = setup_logger(__name__)

# Google Calendar API scopes
SCOPES = ['https://www.googleapis.com/auth/calendar']


class CalendarService(Service):
    def __init__(self):
        super().__init__(logger)
        self.service = None
        self.calendar_id = settings.google_calendar_id or "primary"
        self.credentials_path = settings.google_calendar_credentials_path
        self.token_path = settings.google_calendar_token_path

    async def initialize(self):
        await super().initialize()

        if not self.credentials_path or not os.path.exists(self.credentials_path):
            logger.warning(
                f"Google Calendar credentials not found at {self.credentials_path}. "
                "Calendar sync will be disabled."
            )
            return

        try:
            creds = self._get_credentials()
            if creds and creds.valid:
                self.service = build('calendar', 'v3', credentials=creds)
                logger.info("Google Calendar service initialized successfully")
            else:
                logger.warning("Google Calendar credentials are invalid. Calendar sync will be disabled.")
        except Exception as e:
            logger.error(f"Failed to initialize Google Calendar service: {e}")
            logger.warning("Calendar sync will be disabled.")

    def _get_credentials(self) -> Optional[Credentials]:
        if not self.credentials_path or not os.path.exists(self.credentials_path):
            return None

        if not self.token_path or not os.path.exists(self.token_path):
            logger.warning(
                f"Google Calendar token not found at {self.token_path}. "
                "Run the authentication script: scripts/calendar/setup_auth.sh"
            )
            return None

        creds = None

        try:
            creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)
        except Exception as e:
            logger.warning(f"Failed to load token from {self.token_path}: {e}")
            return None

        if creds and not creds.valid:
            logger.warning(
                "Google Calendar token is invalid and cannot be refreshed. "
                "Run the authentication script: scripts/calendar/setup_auth.sh"
            )
            return None

        return creds

    def _convert_reminders(self, reminder_times: List[int]) -> dict:
        reminders = []

        for minutes in reminder_times:
            if minutes < 60:
                reminders.append({'method': 'popup', 'minutes': minutes})
            elif minutes < 1440:  # Less than 24 hours
                reminders.append({'method': 'popup', 'minutes': minutes})
            else:  # 24 hours or more
                days = minutes // 1440
                reminders.append({'method': 'popup', 'minutes': days * 1440})

        if not reminders:
            reminders.append({'method': 'popup', 'minutes': 15})

        return {'useDefault': False, 'overrides': reminders}

    def _format_datetime_for_google(self, dt: datetime, timezone_str: str) -> str:
        if dt.tzinfo is None:
            tz = pytz.timezone(timezone_str)
            dt = tz.localize(dt)

        return dt.isoformat()

    async def create_event(self, event: Event) -> Optional[str]:
        if not self.service:
            logger.warning("Google Calendar service not initialized. Skipping event creation.")
            return None

        try:
            start_datetime = self._format_datetime_for_google(
                event.event_datetime,
                event.timezone
            )

            if event.end_datetime:
                end_datetime = self._format_datetime_for_google(
                    event.end_datetime,
                    event.timezone
                )
            else:
                end_datetime = self._format_datetime_for_google(
                    event.event_datetime.replace(hour=event.event_datetime.hour + 1),
                    event.timezone
                )

            event_body = {
                'summary': event.event_name,
                'start': {
                    'dateTime': start_datetime,
                    'timeZone': event.timezone,
                },
                'end': {
                    'dateTime': end_datetime,
                    'timeZone': event.timezone,
                },
                'description': event.description or '',
            }

            if event.location:
                event_body['location'] = event.location

            if event.reminder_times:
                event_body['reminders'] = self._convert_reminders(event.reminder_times)

            created_event = self.service.events().insert(
                calendarId=self.calendar_id,
                body=event_body
            ).execute()

            event_id = created_event.get('id')
            event_url = created_event.get('htmlLink')

            logger.info(f"Created Google Calendar event: {event_id} for event {event.id}")

            return event_id

        except HttpError as e:
            logger.error(f"HTTP error creating Google Calendar event: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to create Google Calendar event: {e}")
            return None

    async def update_event(self, event: Event) -> bool:
        if not self.service:
            logger.warning("Google Calendar service not initialized. Skipping event update.")
            return False

        if not event.calendar_event_id:
            logger.warning(f"Event {event.id} has no calendar_event_id. Cannot update.")
            return False

        try:
            existing_event = self.service.events().get(
                calendarId=self.calendar_id,
                eventId=event.calendar_event_id
            ).execute()

            start_datetime = self._format_datetime_for_google(
                event.event_datetime,
                event.timezone
            )

            if event.end_datetime:
                end_datetime = self._format_datetime_for_google(
                    event.end_datetime,
                    event.timezone
                )
            else:
                end_datetime = self._format_datetime_for_google(
                    event.event_datetime.replace(hour=event.event_datetime.hour + 1),
                    event.timezone
                )

            existing_event['summary'] = event.event_name
            existing_event['description'] = event.description or ''
            existing_event['start'] = {
                'dateTime': start_datetime,
                'timeZone': event.timezone,
            }
            existing_event['end'] = {
                'dateTime': end_datetime,
                'timeZone': event.timezone,
            }

            if event.location:
                existing_event['location'] = event.location
            elif 'location' in existing_event:
                existing_event['location'] = ''

            if event.reminder_times:
                existing_event['reminders'] = self._convert_reminders(event.reminder_times)

            updated_event = self.service.events().update(
                calendarId=self.calendar_id,
                eventId=event.calendar_event_id,
                body=existing_event
            ).execute()

            logger.info(f"Updated Google Calendar event {event.calendar_event_id} for event {event.id}")
            return True

        except HttpError as e:
            if e.resp.status == 404:
                logger.warning(f"Google Calendar event {event.calendar_event_id} not found. It may have been deleted.")
            else:
                logger.error(f"HTTP error updating Google Calendar event: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to update Google Calendar event: {e}")
            return False

    async def delete_event(self, event: Event) -> bool:
        if not self.service:
            logger.warning("Google Calendar service not initialized. Skipping event deletion.")
            return False

        if not event.calendar_event_id:
            logger.warning(f"Event {event.id} has no calendar_event_id. Cannot delete.")
            return False

        try:
            self.service.events().delete(
                calendarId=self.calendar_id,
                eventId=event.calendar_event_id
            ).execute()

            logger.info(f"Deleted Google Calendar event {event.calendar_event_id} for event {event.id}")
            return True

        except HttpError as e:
            if e.resp.status == 404:
                logger.warning(f"Google Calendar event {event.calendar_event_id} not found. Already deleted.")
                return True  # Consider it successful if already deleted
            else:
                logger.error(f"HTTP error deleting Google Calendar event: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to delete Google Calendar event: {e}")
            return False

    async def sync_event(self, event: Event) -> bool:
         if event.calendar_event_id:
            success = await self.update_event(event)
            if success:
                try:
                    existing_event = self.service.events().get(
                        calendarId=self.calendar_id,
                        eventId=event.calendar_event_id
                    ).execute()
                    event_url = existing_event.get('htmlLink')
                    if event_url and event_url != event.calendar_url:
                        event.calendar_url = event_url
                        await event.save(update_fields=['calendar_url'])
                except Exception as e:
                    logger.warning(f"Failed to update calendar URL: {e}")
            return success
        else:
            event_id = await self.create_event(event)
            if event_id:
                event.calendar_event_id = event_id
                try:
                    created_event = self.service.events().get(
                        calendarId=self.calendar_id,
                        eventId=event_id
                    ).execute()
                    event.calendar_url = created_event.get('htmlLink', '')
                except Exception as e:
                    logger.warning(f"Failed to get calendar URL: {e}")

                await event.save(update_fields=['calendar_event_id', 'calendar_url'])
                return True
            return False
