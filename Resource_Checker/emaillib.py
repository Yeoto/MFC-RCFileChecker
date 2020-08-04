#-*- coding: utf-8 -*-
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import smtplib
import os

class emaillib:
    def sendMail(self, to_email, file_list):
        to_list = []
        #to_list = to_email[:]
        to_list.append("pyj0827@midasit.com")

        msg = MIMEMultipart()
        message = "Some errors detected in Resource Files what you committed !!"
 
        # setup the parameters of the message
        password = "qkrdbwls00"
        msg['From'] = "pyj0827@midasit.com"
        msg['To'] = ', '.join(to_list)
        msg['Subject'] = "Resource File Errors !"
 
        # add in the message body
        msg.attach(MIMEText(message, 'plain'))

        for f in file_list or []:
            with open(f, "rb") as fil:
                part = MIMEApplication(fil.read(), Name = os.path.basename(f))
            part['Content-Disposition'] = 'attachment; filename="%s"' % os.path.basename(f)
            msg.attach(part)

        #create server
        server = smtplib.SMTP_SSL('smtp.mailplug.co.kr: 465')
 
        # Login Credentials for sending the mail
        server.login(msg['From'], password)
 
        # send the message via the server.
        server.sendmail(msg['From'], msg['To'], msg.as_string())
 
        server.quit()
 
        print("successfully sent email to %s:" % (msg['To']))