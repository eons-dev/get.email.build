import logging
import imaplib
import email
import openai
from ebbs import Builder

class get_email(Builder):
	def __init__(this, name = "Get Email"):
		super().__init__(name)
		this.requiredKWArgs.append('server')
		this.requiredKWArgs.append('username')
		this.requiredKWArgs.append('password')
		
		this.optionalKWArgs['port'] = 993
		this.optionalKWArgs['ssl'] = True
		this.optionalKWArgs['folder'] = 'INBOX'
		this.optionalKWArgs['search'] = '(UNSEEN)'
		this.optionalKWArgs['delete'] = False
		this.optionalKWArgs['mark_as_read'] = False
		this.optionalKWArgs['summarize'] = False
		this.optionalKWArgs['openai_api_key'] = None
		this.optionalKWArgs['openai_engine'] = 'davinci'
		this.optionalKWArgs['openai_max_tokens'] = 500
		this.optionalKWArgs['openai_temperature'] = 0.9
		
		this.mail = []
		

	def Build(this):
		if this.ssl:
			this.mail = imaplib.IMAP4_SSL(this.server, this.port)
		else:
			this.mail = imaplib.IMAP4(this.server, this.port)
		this.mail.login(this.username, this.password)
		this.mail.select(this.folder)
		_, data = this.mail.search(None, this.search)
		for num in data[0].split():
			_, rawMessage = this.mail.fetch(num, '(RFC822)')
			message = email.message_from_bytes(rawMessage[0][1])

			summary = None
			if (this.summarize):
				summary = this.GetEmailSummary(message.get_payload())

			this.mail.append({
				'from': message['From'],
				'to': message['To'],
				'subject': message['Subject'],
				'body': message.get_payload(),
				'summary': summary
			})
			
			# logging.info('Message %s: %s' % (num, msg['Subject']))
			if this.mark_as_read:
				this.mail.store(num, '+FLAGS', '\\Seen')
			if this.delete:
				this.mail.store(num, '+FLAGS', '\\Deleted')
		if this.delete:
			this.mail.expunge()
		this.mail.close()
		this.mail.logout()

		return this.mail
	

	def GetEmailSummary(this, message):
		if this.openai_api_key is None:
			raise Exception('OpenAI API Key is not set')
		openai.api_key = this.openai_api_key
		response = openai.Completion.create(
			engine = this.openai_engine,
			prompt = f"Please summarize the following email.\n {message}",
			max_tokens = this.openai_max_tokens,
			temperature = this.openai_temperature,
			top_p = 1,
			n = 1,
			stream = False,
			logprobs = None,
			stop = None,
			presence_penalty = 0,
			frequency_penalty = 0,
			best_of = 1,
			logit_bias = None,
			echo = False,
			user = None,
			kwargs = None
		)
		return response['choices'][0]['text']