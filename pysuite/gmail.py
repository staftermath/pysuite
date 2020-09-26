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
                gdrive_ids: Optional[List[str]]=None,
                user_id: Optional[str]=None,
                is_html: bool=True):
        msg = self._create_message_skeleton(subject=subject,
                                            sender=sender,
                                            to=to,
                                            cc=cc,
                                            bcc=bcc)
        msg = self._attach_body(msg, body, ids=gdrive_ids, is_html=is_html)
        msg = self._attach_local_files(msg=msg, files=local_files)
        if user_id is None:
            user_id = sender
        response = self._send(user_id=user_id, msg=msg)
        return response

    def _attach_local_files(self, msg: MIMEBase, files: Optional[List[Union[str, PosixPath]]]) -> MIMEBase:
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

    def _attach_body(self, msg: MIMEBase, body: Optional[str], ids: Optional[List[str]], is_html: bool) -> MIMEBase:
        """Attach email body to the msg. If gdrive ids are provided, attach gdrive file hyperlinks in the body. The
        format of the email can be specified to 'html' or 'plain'.

        :param msg: a MIMEBase object.
        :param body: body of the email.
        :param ids: a list of gdrive file ids.
        :param is_html: whether email should be send in html format or plain text format
        :return: a msg with body attached.
        """
        if body is not None:
            body_mime = MIMEText(body, 'html' if is_html else 'plain')
            msg.attach(body_mime)

        msg = self._attach_gdrive_files(msg, ids)
        return msg

    def _attach_gdrive_files(self, msg: MIMEBase, ids: Optional[List[str]]) -> MIMEBase:
        """Attach a list of gdrive files to the msg body in forms of hyper links. If ids is None, no attachment will be
        added.

        :param msg: a MIMEBase object
        :param ids: list of gdrive ids.
        :return: a MIMEBase object with gdrive link attached
        """
        if ids is None:
            return msg

        gdrive_section = """<p>GDrive Attachment</p>\n<ul>\n\t{attached}\n</ul>"""
        link_template = "<li>https://drive.google.com/file/d/{id}</li>"
        attached = []
        for id in ids:
            attached.append(link_template.format(id=id))
        gdrive_section = gdrive_section.format(attached="\n\t".join(attached))
        gdrive_html = MIMEText(gdrive_section, "html")
        msg.attach(gdrive_html)
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
        body = {'raw': urlsafe_b64encode(msg.as_bytes()).decode(),
                'payload': {'mimeType': 'text/html'}}
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
