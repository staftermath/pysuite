"""implement api to access google drive
"""
import logging
from pathlib import PosixPath
from base64 import urlsafe_b64encode
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from typing import Union, Optional, List

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
                local_files: Optional[Union[str, PosixPath]]=None,
                gdrive_files: Optional[List[str]]=None,
                user_id: Optional[str]=None):
        msg = self._create_message_skeleton(subject=subject,
                                            sender=sender,
                                            to=to,
                                            cc=cc,
                                            bcc=bcc)
        msg = self._load_local_files(msg=msg, files=local_files)
        msg = self._load_gdrive_files(msg=msg, ids=gdrive_files)
        msg = self._attach_content(msg=msg, body=body)
        if user_id is None:
            user_id = sender
        response = self._send(user_id=user_id, msg=msg)
        return response

    def _load_local_files(self, msg: MIMEBase, files: Optional[List[Union[str, PosixPath]]]) -> MIMEBase:
        """Attach a list of local files to msg. If files is None, no changes will be made.

        :param msg: a MIMEBase object to attach files with.
        :param files: list of local files to be attached.
        :return: a MIMEBase object with files attached.
        """
        if files is None:
            return msg

        for file in files:
            file = PosixPath(file)
            with open(file, 'rb') as fp:
                attachment = MIMEBase("application", "octet-stream")
                attachment.set_payload(fp.read())
                attachment.add_header('Content-Disposition', 'attachment', filename=file.name)
                msg.attach(attachment)
        return msg

    def _load_gdrive_files(self, msg: MIMEBase, ids: Optional[List[str]]) -> MIMEBase:
        # TODO: implement this method
        return msg

    def _attach_content(self, msg: MIMEBase, body: Optional[str]) -> MIMEBase:
        """Attach a string as body to the msg. If body is None, no change is made.

        :param msg: a MIMEBase object to attach files with.
        :param body: a string containing body of the email.
        :return: a MIMEBase object with body attached if provided.
        """
        # TODO: add function to append signature
        if body is None:
            return msg

        content = MIMEText(body)
        msg.attach(content)
        return msg

    def _create_message_skeleton(self, sender: str, to: Union[str, list], cc: Optional[Union[str, list]]=None,
                                 bcc: Optional[Union[str, list]]=None, subject: Optional[str]=None) -> MIMEMultipart:
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

    def _send(self, user_id: str, msg: MIMEBase) -> dict:
        """Send composed email through API.

        :param user_id: displayed user id.
        :param msg: A composed MIMEBase object.
        :return: dictionary of response
        """
        body = {"raw": urlsafe_b64encode(msg.as_bytes()).decode()}
        response = self._service.send(userId=user_id, body=body).execute()
        logging.debug(response)
        return response

    def _format_recipients(self, recipients: Union[str, list]) -> str:
        """Convert a list of emails to a string accepted by gmail API.

        :param recipients: list of emails.
        :return: a string representing all recipients.
        """
        if not isinstance(recipients, list) and not isinstance(recipients, str):
            raise TypeError(f"recipients must be str or list type. Got {type(recipients)}")

        if isinstance(recipients, str):
            return recipients

        return ", ".join(recipients)
