#!/usr/bin/env python3
# coding=utf-8
"""Sample script that demonstrates `pydocusign` usage for embedded signing.

See also http://iodocs.docusign.com/APIWalkthrough/embeddedSigning

"""
from __future__ import print_function
import hashlib
import os
import uuid
import pydocusign
# from pydocusign.test import fixtures_dir dont think i need it


def getLinkFromPDF():
    try:
        raw_input
    except NameError:
        raw_input = input
    
    
    def prompt(environ_key, description, default):
        try:
            return os.environ[environ_key]
        except KeyError:
            value = raw_input('{description} (default: "{default}"): '.format(
                default=default, description=description))
            if not value:
                return default
            else:
                return value
    
    
    # Get configuration from environment or prompt the user...
    root_url = 'https://demo.docusign.net/restapi/v2'
    username = '353078cd-d966-457b-bcbf-b4541fd26eff'
    password = 'bounder114'
    integrator_key = '886c800a-506f-45c7-8db2-a19ab7d4b0a6'
    callback_url = 'www.google.com'
    signer_return_url = 'www.google.com'
    
    # Create a client.
    client = pydocusign.DocuSignClient(
        root_url=root_url,
        username=username,
        password=password,
        integrator_key=integrator_key,
    )
    
    
    # Login. Updates API URLs in client.
    print("1. GET /login_information")
    login_information = client.login_information()
    print("   Received data: {data}".format(data=login_information))
    
    
    #Prepare list of signers. Ordering matters.
    signers = [
        pydocusign.Signer(
            email='spencer.d.king2@gmail.com',
            name=u'Spencer King',
            recipientId=1,
            clientUserId=str(uuid.uuid4()),  # Something unique in your database.
            tabs=[
                pydocusign.SignHereTab(
                    documentId=1,
                    pageNumber=1,
                    xPosition=100,
                    yPosition=200,
                ),
            ],
            emailSubject='Test PDF Docusign Script',
            emailBody='I am testing the docusign script',
            supportedLanguage='en',
        ),
        pydocusign.Signer(
            email='sking1485@gmail.com',
            name=u'Eduardo Lopez',
            recipientId=2,
            clientUserId=str(uuid.uuid4()),  # Something unique in your database.
            # tabs=[],  # No tabs means user places tabs himself in DocuSign UI.
            tabs=[
                pydocusign.SignHereTab(
                    documentId=1,
                    pageNumber=1,
                    xPosition=100,
                    yPosition=400,
                ),
            ],
            emailSubject='Well docusign is working',
            emailBody='Figured out how to take a text doc, pdf it, and create and send the signing request, woohoo',
            supportedLanguage='en',
        ),
    ]
    
    
    # Create envelope with embedded signing.
    print("2. POST {account}/envelopes")
    event_notification = pydocusign.EventNotification(
        url=callback_url,
    )
    document_path = "./Client_Contracts/Final.pdf"        # os.path.join(fixtures_dir(), 'test.pdf')
    #document_2_path = "./test2.pdf"      # os.path.join(fixtures_dir(), 'test2.pdf')
    with open(document_path, 'rb') as pdf: #, open(document_2_path, 'rb') as pdf_2:
        envelope = pydocusign.Envelope(
            documents=[
                pydocusign.Document(
                    name='HelloWorldTest.pdf',
                    documentId=1,
                    data=pdf,
                )
            ],
            emailSubject='What does this do - 1',  # Title in docusign demo/sent view
            emailBlurb='What does this do - 2',
            eventNotification=event_notification,
            status=pydocusign.Envelope.STATUS_SENT,
            recipients=signers,
        )
        client.create_envelope_from_documents(envelope)
    print("   Received envelopeId {id}".format(id=envelope.envelopeId))
    
    
    # Update recipient list of envelope: fetch envelope's ``UserId`` from DocuSign.
    print("3. GET {account}/envelopes/{envelopeId}/recipients")
    envelope.get_recipients()
    print("   Received UserId for recipient 0: {0}".format(
        envelope.recipients[0].userId))
    print("   Received UserId for recipient 1: {0}".format(
        envelope.recipients[1].userId))
    
    
    # Retrieve embedded signing for first recipient.
    print("4. Get DocuSign Recipient View")
    signing_url = envelope.post_recipient_view(
        envelope.recipients[0],
        returnUrl=signer_return_url)
    print("   Received signing URL for recipient 0: {0}".format(signing_url))
    signing_url = envelope.post_recipient_view(
        envelope.recipients[1],
        returnUrl=signer_return_url)
    print("   Received signing URL for recipient 1: {0}".format(signing_url))
    
    
    # Download signature documents.
    print("5. List signature documents.")
    document_list = envelope.get_document_list()
    print("   Received document list: {0}".format(document_list))
    print("6. Download documents from DocuSign.")
    for signed_document in document_list:
        document = envelope.get_document(signed_document['documentId'])
        document_sha = hashlib.sha1(document.read()).hexdigest()
        print("   Document SHA1: {0}".format(document_sha))
    print("7. Download signature certificate from DocuSign.")
    document = envelope.get_certificate()
    document_sha = hashlib.sha1(document.read()).hexdigest()
    print("   Certificate SHA1: {0}".format(document_sha))
    
    URLS = [envelope.post_recipient_view( # Recipient URL 1
        envelope.recipients[0],
        returnUrl=signer_return_url), 
        envelope.post_recipient_view(     # Recipient URL 2
        envelope.recipients[1],
        returnUrl=signer_return_url)]
        
    return URLS    
    