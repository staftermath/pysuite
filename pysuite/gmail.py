"""implement api to access google drive
"""
import logging
from pathlib import PosixPath
from base64 import urlsafe_b64encode
import mimetypes
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from typing import Union, Optional

from googleapiclient.discovery import Resource

MINE_TYPE_TO_CLASS_MAP = {
    "text": MIMEText,
    "image": MIMEImage,
    "audio": MIMEAudio
}


class GMail:

    def __init__(self, service: Resource):
        self._service = service.users().messages()

    def compose(self, sender: str, to: Union[str, list], cc: Optional[Union[str, list]]=None,
                bcc: Optional[Union[str, list]]=None, body: Optional[str]=None, subject: Optional[str]=None,
                attachment: Optional[Union[str, PosixPath]]=None,
                user_id: Optional[str]=None):
        msg = self._create_message_skeleton(subject=subject,
                                            sender=sender,
                                            to=to,
                                            cc=cc,
                                            bcc=bcc)
        if attachment is not None:
            attachment = PosixPath(attachment)
            msg = self._load_attachment(msg=msg, file=attachment)
        if body is not None:
            msg = self._attach_content(msg=msg, body=body)
        if user_id is None:
            user_id = sender
        response = self._send(user_id=user_id, msg=msg)
        return response

    def _load_attachment(self, msg: MIMEBase, file: PosixPath):
        content_type, encoding = mimetypes.guess_type(file)
        if content_type is None or encoding is not None:
            content_type = 'application/octet-stream'
        main_type, sub_type = content_type.split('/', 1)
        with open(file, 'rb') as fp:
            try:
                attachment = MINE_TYPE_TO_CLASS_MAP[main_type](fp, _subtype=sub_type)
            except KeyError:
                logging.warning("Cannot determine the attachment type. Using Base type instead.")
                attachment = MIMEBase(fp, _subtype=sub_type)

        attachment.add_header('Content-Disposition', 'attachment', filename=file.name)
        msg.attach(attachment)
        return msg

    def _attach_content(self, body: str, msg: MIMEBase):
        # TODO: add function to append signature
        content = MIMEText(body)
        msg.attach(content)
        return msg

    def _create_message_skeleton(self, sender: str, to: Union[str, list], cc: Optional[Union[str, list]]=None,
                                 bcc: Optional[Union[str, list]]=None, subject: Optional[str]=None):
        message = MIMEMultipart()
        message['from'] = sender
        message['to'] = self._format_recipients(to)
        if subject is not None:
            message['subject'] = subject
        if cc is not None:
            message['cc'] = self._format_recipients(cc)
        if bcc is not None:
            message['bcc'] = self._format_recipients(cc)
        return message

    def _send(self, user_id: str, msg: MIMEBase):
        body = {"raw": urlsafe_b64encode(msg.as_bytes()).decode()}
        response = self._service.send(userId=user_id, body=body).execute()
        logging.debug(response)
        return response

    def _format_recipients(self, recipients: Union[str, list]) -> str:
        if not isinstance(recipients, list) and not isinstance(recipients, str):
            raise TypeError(f"recipients must be str or list type. Got {type(recipients)}")

        if isinstance(recipients, str):
            return recipients

        return ", ".join(recipients)
