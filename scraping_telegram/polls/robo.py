from iqoptionapi.stable_api import IQ_Option
from datetime import date
from datetime import datetime, timedelta
from dateutil import tz
from telegram.bot import Bot
import time, json, requests
import time
import mysql.connector
import sys
import os
import threading
import time
import logging
import psutil
import os




##------------------------FUNCAO PARA MANDAR MSG P TELEGRAM -------------------##
# FUNCAO PARA VERIFICAR SE VAI COMPRAR BINARIA OU DIGITAL



def MensagemTelegram(texto):
   
	try:
		
		API_TELEGRAM = Bot(token='1302956221:AAGaiW6G9ChlCax_EJMWH3xR7qu25iTp1D4')
		ID = API_TELEGRAM.send_message(chat_id='-1001332737008', text=texto,parse_mode= 'Markdown')
		return (ID['message_id'])

	except Exception as e:
		print(e)   

def MensagemTelegramEd(id_menssagem, texto):
   
	try:
		
		API_TELEGRAM = Bot(token='1302956221:AAGaiW6G9ChlCax_EJMWH3xR7qu25iTp1D4')
		API_TELEGRAM.editMessageText(chat_id='-1001332737008', message_id= id_menssagem, text=texto, parse_mode= 'Markdown')

	except Exception as e:
		print(e)  

##----------------------------- CONEXAO MYSQL -----------------------------##

mydb = mysql.connector.connect(
  host="localhost",
  user="root",
  password="",
  database="iqoption"
)

con = mysql.connector.connect(
  host="localhost",
  user="root",
  password="",
  database="iqoption"
)

con1 = mysql.connector.connect(
  host="localhost",
  user="root",
  password="",
  database="iqoption"
)

mydb.autocommit = True
con.autocommit = True
con1.autocommit = True

id_mensagem_inicial = 0 # variavel com id da mensagem do telegram inicial
id_mensagem_verifica = 0 # variavel com id da mensafem do telegram verificacoes


##----------------------------- CONEXAO APPI -----------------------------##

# Abaixo deve ser inserido o login e senha
API = IQ_Option('iurysal@hotmail.com', 'Iwsl#8462365')

# Responsavel por fazer a primeira conexao
API.connect()

# Responsavel por alterar o modo da conta entre TREINAMENTO e REAL
API.change_balance('PRACTICE') # PRACTICE / REAL

# Looping para realizar a verificacao se a API se conectou corretamente ou se deve tentar se conectar novamente
while True:
	if API.check_connect() == False:
		print('Erro ao se conectar')
		
		# No video e apresentado a funcao reconnect(), mas nas versao mais novas da API ela nao esta mais disponivel, sendo assim deve ser utilizado API.connect() para realizar a conexao novamente
		API.connect()
	else:
		print('Conectado com Sucesso! ')
		id_mensagem_inicial = MensagemTelegram('✅ Conectado com sucesso!')
		break
	
	time.sleep(1)
	
##-------------------------------------------------------------------------------##





##----------------------------- DATA ATUAL --------------------------------------##
# RETORNA A DATA ATUAL PARA COMPARACAO COM OS SINAIS NO BANCO DE DADOS
def DiaSemana():
	data_atual = date.today()
	dia_semana = datetime.today().weekday()
	return dia_semana

##----------------------------- DATA ATUAL --------------------------------------##
# RETORNA A DATA ATUAL PARA COMPARACAO COM OS SINAIS NO BANCO DE DADOS
def PegaDataAtual():

	data_atual = date.today()
	data_em_texto = data_atual.strftime('%d/%m/%Y')
	hora_em_texto = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
	hora_em_texto = hora_em_texto[11:19]
	return data_em_texto

##----------------------------- HORA ATUAL --------------------------------------##
# RETORNA A HORA ATUAL PARA COMPARACAO COM OS SINAIS NO BANCO DE DADOS

def PegaHoraAtual():
	data_atual = date.today()
	hora_em_texto = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
	hora_em_texto = hora_em_texto[11:19]
	return hora_em_texto

##--------------------------- FUNCAO UPDATE -------------------------------------##
# FAZ O UPDATE NOS SINAIS, PARA OS STATUS DE 'GALE1, 'GALE2', 'PROCESSAMENTO'....

def update(sql):
	
		mydb = mysql.connector.connect(
		  host="localhost",
		  user="root",
		  password="",
		  database="iqoption"
		)

		mycursor = mydb.cursor()
		mycursor.execute(sql)
		mydb.commit()
		mycursor.close()
		mydb.close()

##--------------------------- CONVERTER TIMESTAMP -------------------------------##
# CONVERTE O VAR EM TIMESTAMP

def timestamp_converter(x):
	hora = datetime.strptime(datetime.utcfromtimestamp(x).strftime('%Y-%m-%d %H:%M:%S'), '%Y-%m-%d %H:%M:%S')
	hora = hora.replace(tzinfo=tz.gettz('GMT'))
	
	return str(hora.astimezone(tz.gettz('America/Sao Paulo')))[:-6]

##--------------------------- VERIFICAR 3 VELAS ---------------------------------##
# VERIFICA SE AS ULTIMAS 3 VELAS SE É DA MESMA COR DA COMPRA/VENDA

def verificar_velas(par, timeframe, operacao, API):

	vela = API.get_candles(par, int(timeframe)*60, 4, time.time())

	aux_verde = 0 
	aux_vermelho = 0

	if (vela != None):
		for velas in vela:
			
			if( ( float(velas['open']) - float(velas['close']) ) < 0): # vela verde
				aux_verde = aux_verde + 1
			   
			if( ( float(velas['open']) - float(velas['close']) ) > 0): # vela vermelha
				 aux_vermelho = aux_vermelho + 1

	print('verde:',aux_verde, 'vermelhea:',aux_vermelho)
	print(operacao)

	if (operacao=='call' and aux_verde==4):
		 return 'nao_compra'
	elif (operacao=='put' and aux_vermelho==4):
		 return 'nao_compra'
	else:
		 return 'compra'
		
##--------------------------- FUNCAO STOP_GAIN ----------------------------------##
# VERIFICA SE JA BATEU A META DO DIA E SAI DO MERCADO

def get_stop_gain():
	
		data_atual = PegaDataAtual()
		balanco_atual = API.get_balance()
		balanco_inicial = get_balanco_inicial()
		stop_gain = 0
		lucro=0
		porcentagem=0
		
		mydb = mysql.connector.connect(
			  host="localhost",
			  user="root",
			  password="",
			  database="iqoption"
			)
		mydb.autocommit = True
		mycursor = mydb.cursor()
		mycursor.execute("select * from balanco_inicial where balanco_inicial.data='"+data_atual+"'")
		checkBalance= mycursor.fetchone()
		
		if (checkBalance == None): #nao existe balanco do dia atual
			
			balanco_dia = balanco_atual
			sql = "INSERT INTO balanco_inicial (id, data, valor) VALUES ('0', '"+str(data_atual)+"', "+str(balanco_atual)+");"
			update(sql)
				
		
		mycursor.execute("select stop_gain from config")  # VERIFICA O STOP_GAIN NA TABELA CONFIG
		myresult= mycursor.fetchall()
		
		for x in myresult:
				stop_gain = x[0]
				
		
		sql = "update config set config.balanco_atual="+str(balanco_atual)+" where config.id=1"
		update(sql)

		mycursor.execute("select sum(lucro) from sinais where sinais.data='"+str(data_atual)+"'   ")  # VERIFICA O LUCRO NO DIA
		myresult= mycursor.fetchall()
		
		for x in myresult:
			if(x[0]!=None):
				lucro = x[0]

		
		if(lucro!=0):
			porcentagem = (lucro*100)/balanco_inicial

		if( porcentagem >= stop_gain ):
			#stop gain batido, sair do mercado
			return True
		else:
			#stop gain nao batido, continuar no mercado
			return False
		

		mycursor.close()
		mydb.close()
##--------------------------- VERIFICA STOP_LOSS -----------------------------##
# FUNCAO PARA VERIFICAR SE VAI SAIR OU CONTINUAR NO MERCADO 

def get_stop_loss():

	mydb = mysql.connector.connect(
	  host="localhost",
	  user="root",
	  password="",
	  database="iqoption"
	)

	mydb.autocommit = True
	mycursor = mydb.cursor()

	stop_loss = 0
	data = PegaDataAtual()
	balanco_inicial=get_balanco_inicial()

	mycursor.execute("select stop_loss from config")  # VERIFICA O STOP_GAIN NA TABELA CONFIG
	myresult = mycursor.fetchall()
		
	for x in myresult:
			stop_loss= x[0]

	
	sql="select DISTINCT (select COUNT(sinais.id) from sinais where sinais.STATUS_FINAL='RED' and SINAIS.DATA='"+str(data)+"') as red , (select sum(sinais.lucro) from sinais where SINAIS.DATA='"+str(data)+"') as lucro FROM sinais WHERE SINAIS.DATA='"+str(data)+"'"
	
	mycursor.execute(sql)
	myresult = mycursor.fetchall()

	
	lucro=0
	qtde_red=0

	for x in myresult:
			
			if(x[0]!=None):
				qtde_red = int(x[0])
			if(x[1]!=None):
				lucro = float(x[1])


	if(qtde_red >= 2 and (lucro) < ((stop_loss*balanco_inicial)/100)*(-1)): 
		return True #sair do mercado
	else:
		return False #continuar no mercado

	mycursor.close()
	mydb.close()

##--------------------------- PEGA RESUMO DEPOS DA OP ---------------------------##
# ENVIA RESUMO PELO TELEGRAM

def resumo_apos_op():

		mydb = mysql.connector.connect(
		  host="localhost",
		  user="root",
		  password="",
		  database="iqoption"
		)
		
		green = 0
		red = 0
		fechada = 0
		sem_gale= 0
		um_gale=0
		dois_gale=0
		lucro=0
		balanco_atual=API.get_balance()
		data=PegaDataAtual()
		

		mydb.autocommit = True
		mycursor = mydb.cursor()
		mycursor.execute("select DISTINCT"+
		" (select count(sinais.STATUS_FINAL) from sinais where sinais.DATA='"+str(data)+"' and sinais.STATUS_FINAL='GREEN') as green, "+
		" (select count(sinais.STATUS_FINAL) from sinais where sinais.DATA='"+str(data)+"' and sinais.STATUS_FINAL='RED') as red,"+
		" (select count(sinais.STATUS_FINAL) from sinais where sinais.DATA='"+str(data)+"' and sinais.STATUS_FINAL='FECHADA') as fechada,"+
		" (select count(sinais.STATUS_FINAL) from sinais where sinais.DATA='"+str(data)+"' and sinais.LUCRO!=0 and sinais.GALE_1=0 and sinais.GALE_2=0) as sem_gale,"+
		" (select count(sinais.STATUS_FINAL) from sinais where sinais.DATA='"+str(data)+"' and sinais.LUCRO!=0 and sinais.GALE_1=1 and sinais.GALE_2=0) as um_gale,"+
		" (select count(sinais.STATUS_FINAL) from sinais where sinais.DATA='"+str(data)+"' and sinais.LUCRO!=0 and sinais.GALE_1=1 and sinais.GALE_2=1) as dois_gale,"+
		" (select sum(sinais.LUCRO) from sinais where sinais.DATA='"+str(data)+"') as lucro"+
		" from sinais where sinais.DATA='"+str(data)+"'")
		myresult = mycursor.fetchall()
		
		for x in myresult:
				green = x[0]
				red = x[1]
				fechada = x[2]
				sem_gale = x[3]
				um_gale = x[4]
				dois_gale = x[5]
				lucro = round(x[6],2)

		porcentagem = round((lucro*100)/float(get_balanco_inicial()),2)
		texto = "✅ Green: "+str(green)+"\n🛑 Red: "+str(red)+"\n🔒 Fechada: "+str(fechada)+"\n\n🥇 Sem Gale: "+str(sem_gale)+"\n🥈 Um Gale: "+str(um_gale)+"\n🥉 Dois Gales: "+str(dois_gale)+"\n\n 🤑 Stop Gain: "+str(get_stop_gain())+"\n 😫 Stop Loss: "+str(get_stop_loss())+"\n\n💰 Balanco Inicial: "+str(get_balanco_inicial())+"\n💶 Balanço Atual: "+str(balanco_atual)+"\n💸 Lucro: "+str(lucro)+" ("+str(porcentagem)+"%)"
		MensagemTelegram(texto)
					  
##--------------------------- PEGA QUANTIDADE DE GALE --------------------------##
# VAI NO BANCO DE DADOS E PEGA A QUANTIDADE DE GALE NAS CONFIGURACOES

def get_gale():
	
	mydb = mysql.connector.connect(
		  host="localhost",
		  user="root",
		  password="",
		  database="iqoption"
		)
	gale = 0
	mydb.autocommit = True
	mycursor = mydb.cursor()
	mycursor.execute("select config.gale from config")
	myresult = mycursor.fetchall()
	
	for x in myresult:
			gale = x[0]
	
	mycursor.close()
	mydb.close()
	return gale

##-------------------- RETORNA BALANCO INICIAL DO DIA --------------------------##
# VAI NO BANCO DE DADOS E PEGA A QUANTIDADE DE GALE NAS CONFIGURACOES

def get_balanco_inicial():
	
	mydb = mysql.connector.connect(
		  host="localhost",
		  user="root",
		  password="",
		  database="iqoption"
		)
	balanco_inicial = 0
	mydb.autocommit = True
	mycursor = mydb.cursor()
	mycursor.execute("select balanco_inicial.valor from balanco_inicial where balanco_inicial.data='"+str(PegaDataAtual())+"' ")
	myresult = mycursor.fetchall()
	
	for x in myresult:
			balanco_inicial = x[0]

	mycursor.close()
	mydb.close()

	return balanco_inicial

##--------------------------- PEGA VALOR DE ENTRADA DOS PARES ------------------##
# VAI NO BANCO DE DADOS E PEGA O VALOR INICIAL E CONVERTE EM 1%

def get_valor_entrada():
	
	mydb = mysql.connector.connect(
		  host="localhost",
		  user="root",
		  password="",
		  database="iqoption"
		)
	valor_entrada = 0
	mydb.autocommit = True
	mycursor = mydb.cursor()
	mycursor.execute("select valor from balanco_inicial where balanco_inicial.data='"+PegaDataAtual()+"' ")
	myresult= mycursor.fetchall()

	for x in myresult:
			valor_entrada = x[0]
	
	valor_entrada = round((float(valor_entrada)/100)*1,2)

	mycursor.close()
	mydb.close()

	return valor_entrada

##--------------------------- GRAVA BALANCO DO DIA -----------------------------##
# GRAVA BALANCO DO DIA NO BANCO DE DADOS

def put_balanco_atual():
	
	balanco_atual = API.get_balance()
	sql = "update config set config.balanco_atual="+str(balanco_atual)+" where config.id=1"
	update(sql)

def get_balanco_atual():
   balanco_atual = API.get_balance()
   return str(balanco_atual)


##--------------------------- GRAVA LOG NO ARQ TXT ----------------------------##
# GRAVA LOG NO ARQUIVO TXT NA RAIZ DO PROJETO  
	
def grava_log(texto):
	
	try:
		arquivo = open('/Users/iurywallysson/Python/Iqoption/iqoptionapi-master/log.txt','a')
		arquivo.write(texto + "\n")
		arquivo.close()
	except:
		print('erro no arquivo txt')

##--------------------------- VERIFICA PAYOUT ---------------------------------##
# FFUNCAO PARA VERIFICAR PARIDADE DE TERMINADA MOEDA

def get_payout(par, tipo, timeframe):
	if tipo == 'turbo':
		a = API.get_all_profit()
		
		return int(100 * a[par]['turbo'])
		
	elif tipo == 'digital':
	
		API.subscribe_strike_list(par, timeframe)
		while True:
			d = API.get_digital_current_profit(par, timeframe)
			if d != False:
				d = int(d)
				break
			time.sleep(1)
		API.unsubscribe_strike_list(par, timeframe)
		return d

##--------------------------- VERIFICA TIPO ENTRADA ---------------------------##
# FUNCAO PARA VERIFICAR SE VAI COMPRAR BINARIA OU DIGITAL

def put_tipo_entrada(paridade,hora,timeframe,id_sinal,id_mensagem):

	

	payout_turbo = 0
	aberta_turbo = False
	payout_digital = 0
	aberta_digital = False

	aux = ''

	try:
		
		par = API.get_all_open_time()
	
		if par['turbo'][str(paridade)]['open'] == True:
			aberta_turbo = True
			payout_turbo = int(get_payout(str(paridade), 'turbo', int(timeframe)))

		if par['digital'][str(paridade)]['open'] == True:
			aberta_digital = True
			payout_digital = int(get_payout(str(paridade), 'digital', int(timeframe)))

		#print('payout binaria: ',payout_turbo,'Aberta: ',aberta_turbo)
		#print('payout digital: ',payout_digital,'Aberta: ',aberta_digital)

		if (payout_turbo>payout_digital and aberta_turbo== True):
			aux = 'BINARIA'
		if (payout_digital>payout_turbo and aberta_digital== True):
			aux = 'DIGITAL'
		if(aberta_turbo==False and aberta_digital==False):
			aux = 'FECHADA'
		if (timeframe==15 or aux==''):
			aux = 'BINARIA'

	except:
		print('ERRO NA VERIFICACAO DA ENTRADA')
		

	print('MOEDA:',str(paridade),'\nHORA:',str(hora),'\n* ENTRADA DO TIPO:',aux,'\n')
	MensagemTelegramEd(id_mensagem,'💲 MOEDA: '+paridade+'\n⏰ HORA: '+str(hora)+'\n➡️ ENTRADA DO TIPO: '+aux)

	sql = "update sinais set sinais.TIPO='"+str(aux)+"' where sinais.id="+str(id_sinal)+" "
	update(sql)



def analisar_velas_dias_anteriores(data='20/07/2020', dias = 10):

	mydb = mysql.connector.connect(
	  host="localhost",
	  user="root",
	  password="",
	  database="iqoption"
	)

	mydb.autocommit = True
	mycursor = mydb.cursor()

	par = ''
	hora = ''
	

	mycursor.execute("select sinais.moeda,sinais.hora from sinais where data='"+str(data)+"'") 
	myresult = mycursor.fetchall()
		
	for x in myresult:
			par= x[0]
			hora= x[1]

			now = '2020-07-20 '+str(hora)
			y=0
			aux_verde = 0 
			aux_vermelho = 0
			aux_igual = 0
			aux='NAO'
			porc=0
			for y in range(dias):

				date_time_obj = datetime.strptime(now, '%Y-%m-%d %H:%M:%S')
				date_time_obj = date_time_obj - timedelta(days=y)
				timestamp = datetime.timestamp(date_time_obj)


				vela = API.get_candles(str(par), 60, 1, timestamp)


				for velas in vela:

				   # print(float(velas['open']),float(velas['close']))
				
					if( ( float(velas['open']) - float(velas['close']) ) < 0): # vela verde
						aux_verde = aux_verde + 1
					if( ( float(velas['open']) - float(velas['close']) ) > 0): # vela vermelha
						 aux_vermelho = aux_vermelho + 1
					if( ( float(velas['open']) - float(velas['close']) ) == 0): # vela vermelha
						 aux_igual = aux_igual + 1

				if((aux_vermelho*100)/dias >= 60):
					aux = 'SIM'
				if((aux_verde*100)/dias >= 60):
					aux = 'SIM'

				if((aux_vermelho*100)/dias>(aux_verde*100)/dias):
					porc =(aux_vermelho*100)/dias
				else:
					 porc =(aux_verde*100)/dias


			print ('PAR:',par,'HORA:',hora,'----- verde',aux_verde,'vermelha',aux_vermelho,'igual',aux_igual,'PORCENTAGEM',porc,'====',aux)

def noticas(paridade, minutos_lista):
	objeto = json.loads(texto)

	# Verifica se o status code é 200 de sucesso
	if response.status_code != 200 or objeto['success'] != True:
		print('Erro ao contatar notícias')

	# Pega a data atual
	data = datetime.now()
	tm = tz.gettz('America/Sao Paulo')
	data_atual = data.astimezone(tm)
	data_atual = data_atual.strftime('%Y-%m-%d')

	# Varre todos o result do JSON
	for noticia in objeto['result']:
		# Separa a paridade em duas Ex: AUDUSD separa AUD e USD para comparar os dois
		paridade1 = paridade[0:3]
		paridade2 = paridade[3:6]
		
		# Pega a paridade, impacto e separa a data da hora da API
		moeda = noticia['economy']
		impacto = noticia['impact']
		atual = noticia['data']
		data = atual.split(' ')[0]
		hora = atual.split(' ')[1]
		
		# Verifica se a paridade existe da noticia e se está na data atual
		if moeda == paridade1 or moeda == paridade2 and data == data_atual:
			formato = '%H:%M:%S'
			d1 = datetime.strptime(hora, formato)
			d2 = datetime.strptime(minutos_lista, formato)
			dif = (d1 - d2).total_seconds()
			# Verifica a diferença entre a hora da noticia e a hora da operação
			minutesDiff = dif / 60
		
			# Verifica se a noticia irá acontencer 30 min antes ou depois da operação
			if minutesDiff >= -30 and minutesDiff <= 0 or minutesDiff <= 30 and minutesDiff >= 0:
				return impacto, moeda, hora, True
			else:
				return 0, 0, 0, False
		else:
			return 0, 0, 0, False
	
		
##--------------------------- CLASSE THREAD ---------------------------- ------##
# CLASSE ONDE É FEITO A COMPRA DOS PARES E REALIZADO OS GALES
# CADA SINAL É ABERTO UMA CLASSE 'THREAD'
	
class comprar_binario(threading.Thread):
	
	def __init__( self, con, API, valor, par, direcao, timeframe, id_sinal, hora, data, gale):
		threading.Thread.__init__(self)
		self.valor=valor
		self.par=par
		self.direcao=direcao
		self.timeframe=timeframe
		self.API = API
		self.id_sinal=id_sinal
		self.con = con
		self.rs = rs
		self.hora = hora
		self.data= data
		self.gale = gale
		
	def run(self):
		
		sql= "UPDATE sinais SET sinais.processando=1 WHERE sinais.ID ='"+str(self.id_sinal)+"'"
		update(sql)
		
		status,id = self.API.buy(self.valor, self.par, self.direcao, self.timeframe) ## tenta comprar BINARIA

		texto = '🕵️‍♂️ *SINAL MISTER OB - BINARIO*\n\n⏰ HORA: '+self.hora+'\n🗓 DATA: '+self.data+'\n🧭 GRAFICO: '+str(self.timeframe)+'\n💲 MOEDA: '+self.par+'\n🔹 OPERACAO: '+self.direcao+'\n\n🥇 *PRIMEIRA TENTATIVA:* Sem Gale\n🥈 *SEGUNDA TENTATIVA:*\n🥉 *TERCEIRA TENTATIVA:*\n\n💸 *LUCRO*: 0\n♻️ *RESULTADO:* Aguardando...\n'
		print(texto)
		grava_log(texto)
		id_mensagem = MensagemTelegram(texto)

		if status:

			resultado,lucro = self.API.check_win_v4(id)

			
			texto = '🕵️‍♂️ *SINAL MISTER OB - BINARIO*\n\n⏰ HORA: '+self.hora+'\n🗓 DATA: '+self.data+'\n🧭 GRAFICO: '+str(self.timeframe)+'\n💲 MOEDA: '+self.par+'\n🔹 OPERACAO: '+self.direcao+'\n\n🥇 *PRIMEIRA TENTATIVA:* '+ str( '✅' if resultado=='win' else '🚫' )+'\n🥈 *SEGUNDA TENTATIVA:*\n🥉 *TERCEIRA TENTATIVA:*\n\n💸 *LUCRO:* '+str(lucro)+'\n♻️ *RESULTADO:* '+ str( '✅✅✅' if resultado=='win' else '🚫🚫🚫' )+'\n'
			print(texto)
			grava_log(texto)
			MensagemTelegramEd(id_mensagem,texto)

			if resultado == 'win':

				sql= "UPDATE sinais SET sinais.STATUS_FINAL='GREEN', sinais.LUCRO='"+str(lucro)+"' WHERE sinais.ID ='"+str(self.id_sinal)+"'"
				update(sql)

			else:

				status1,id = self.API.buy(self.valor*2.2, self.par, self.direcao, self.timeframe)
				texto = '🕵️‍♂️ *SINAL MISTER OB - BINARIO* \n\n⏰ HORA: '+self.hora+'\n🗓 DATA: '+self.data+'\n🧭 GRAFICO: '+str(self.timeframe)+'\n💲 MOEDA: '+self.par+'\n🔹 OPERACAO: '+self.direcao+'\n\n🥇 *PRIMEIRA TENTATIVA:* '+ str( '✅' if resultado=='win' else '🚫' )+'\n🥈 *SEGUNDA TENTATIVA:* 1 Gale\n🥉 *TERCEIRA TENTATIVA:*\n\n💸 *LUCRO:* 0\n♻️ *RESULTADO:* Aguardando...\n'
			   
				print(texto)
				grava_log(texto)
				MensagemTelegramEd(id_mensagem,texto)

				sql= "UPDATE sinais SET sinais.GALE_1=1 WHERE sinais.ID ='"+str(self.id_sinal)+"'"
				update(sql)

				if status1:

					resultado1,lucro1 = self.API.check_win_v4(id)
					texto = '🕵️‍♂️ *SINAL MISTER OB - BINARIO*\n\n⏰ HORA: '+self.hora+'\n🗓 DATA: '+self.data+'\n🧭 GRAFICO: '+str(self.timeframe)+'\n💲 MOEDA: '+self.par+'\n🔹 OPERACAO: '+self.direcao+'\n\n🥇 *PRIMEIRA TENTATIVA:* '+ str( '✅' if resultado=='win' else '🚫' )+'\n🥈 *SEGUNDA TENTATIVA:* '+ str( '✅' if resultado1=='win' else '🚫' )+'\n🥉 *TERCEIRA TENTATIVA:*\n\n💸 *LUCRO:* '+str(lucro1-self.valor)+'\n♻️ *RESULTADO:* '+ str( '✅✅✅' if resultado1=='win' else '🚫🚫🚫' )+'\n'
					
					print(texto)
					grava_log(texto)
					MensagemTelegramEd(id_mensagem,texto)

					if resultado1 == 'win':

						sql= "UPDATE sinais SET sinais.STATUS_FINAL='GREEN', sinais.LUCRO='"+str(lucro1-self.valor)+"' WHERE sinais.ID ='"+str(self.id_sinal)+"'"
						update(sql)

					else:

						if (self.gale==1): ## SE GALE FOR IGUAL A 1, A FUNCAO PARA E RETORNAR RED

							sql= "UPDATE sinais SET sinais.STATUS_FINAL='RED', sinais.LUCRO='"+str(0-(self.valor+(self.valor*2.2)))+"' WHERE sinais.ID ='"+str(self.id_sinal)+"'"
							update(sql)

						else: # SE FOR 2 OU MAIS, ELA CONTINUA A FUNCAO

							status2,id = self.API.buy(self.valor*4, self.par, self.direcao, self.timeframe)

							texto = '🕵️‍♂️ *SINAL MISTER OB - BINARIO*\n\n⏰ HORA: '+self.hora+'\n🗓 DATA: '+self.data+'\n🧭 GRAFICO: '+str(self.timeframe)+'\n💲 MOEDA: '+self.par+'\n🔹 OPERACAO: '+self.direcao+'\n\n🥇 *PRIMEIRA TENTATIVA:* '+ str( '✅' if resultado=='win' else '🚫' )+'\n🥈 *SEGUNDA TENTATIVA:* '+ str( '✅' if resultado1=='win' else '🚫' )+'\n🥉 *TERCEIRA TENTATIVA:* 2 Gale\n\n💸 *LUCRO:* 0\n♻️ *RESULTADO:* Aguardando...\n'
							
							print(texto)
							grava_log(texto)
							MensagemTelegramEd(id_mensagem,texto)

							sql= "UPDATE sinais SET sinais.GALE_2=1 WHERE sinais.ID ='"+str(self.id_sinal)+"'"
							update(sql)


							if status2:

								resultado2,lucro2 = self.API.check_win_v4(id)

								texto = '🕵️‍♂️ *SINAL MISTER OB - BINARIO*\n\n⏰ HORA: '+self.hora+'\n🗓 DATA: '+self.data+'\n🧭 GRAFICO: '+str(self.timeframe)+'\n💲 MOEDA: '+self.par+'\n🔹 OPERACAO: '+self.direcao+'\n\n🥇 *PRIMEIRA TENTATIVA:* '+ str( '✅' if resultado=='win' else '🚫' )+'\n🥈 *SEGUNDA TENTATIVA:* '+ str( '✅' if resultado1=='win' else '🚫' )+'\n🥉 *TERCEIRA TENTATIVA:* '+ str( '✅' if resultado2=='win' else '🚫' )+'\n\n💸 *LUCRO:* '+str(lucro2-((self.valor*2.2)+self.valor))+'\n♻️ *RESULTADO:* '+ str( '✅✅✅' if resultado2=='win' else '🚫🚫🚫' )+'\n'
								print(texto)
								grava_log(texto)
								MensagemTelegramEd(id_mensagem,texto)

								if resultado2 == 'win':

									sql= "UPDATE sinais SET sinais.STATUS_FINAL='GREEN', sinais.LUCRO='"+str(lucro2-((self.valor*2.2)+self.valor))+"' WHERE sinais.ID ='"+str(self.id_sinal)+"'"
									update(sql)

								else:

									sql= "UPDATE sinais SET sinais.STATUS_FINAL='RED', sinais.LUCRO='"+str(0-(self.valor+(self.valor*2.2)+(self.valor*4)))+"' WHERE sinais.ID ='"+str(self.id_sinal)+"'"
									update(sql)


			sql= "UPDATE sinais SET sinais.processando=2 WHERE sinais.ID ='"+str(self.id_sinal)+"'"
			update(sql)
			put_balanco_atual() ## APOS A OPERACAO, É VERIFICADO O BALANCO
			resumo_apos_op()


		elif ( id != None):  

			 if ('Cannot purchase an option' in id or 'Não foi possível abrir uma negociação' in id  ):
					texto = '🕵️‍♂️ *SINAL MISTER OB - BINARIO*\n\n⏰ HORA: '+self.hora+'\n🗓 DATA: '+self.data+'\n🧭 GRAFICO: '+str(self.timeframe)+'\n💲 MOEDA: '+self.par+'\n🔹 OPERACAO: '+self.direcao+'\n\n🥇 *PRIMEIRA TENTATIVA:*\n🥈 *SEGUNDA TENTATIVA:*\n🥉 *TERCEIRA TENTATIVA:*\n\n🚫ERRO AO COMPRAR = '+str(id)+'\n'
					
					print(texto)
					grava_log(texto)
					MensagemTelegramEd(id_mensagem,texto)
					sql = sql= "UPDATE sinais SET sinais.STATUS_FINAL='FECHADA', sinais.PROCESSANDO=3 WHERE sinais.ID ='"+str(self.id_sinal)+"'"
					update(sql)

		elif ( id == None): 
			texto = '🕵️‍♂️ *SINAL MISTER OB - BINARIO*\n\n⏰ HORA: '+self.hora+'\n🗓 DATA: '+self.data+'\n🧭 GRAFICO: '+str(self.timeframe)+'\n💲 MOEDA: '+self.par+'\n🔹 OPERACAO: '+self.direcao+'\n\n🥇 *PRIMEIRA TENTATIVA:*\n🥈 *SEGUNDA TENTATIVA:*\n🥉 *TERCEIRA TENTATIVA:*\n\n🚫ERRO AO COMPRAR = '+str(id)+'\n'
			print(texto)
			grava_log(texto)
			MensagemTelegramEd(id_mensagem,texto)
			sql = sql= "UPDATE sinais SET sinais.STATUS_FINAL='FECHADA', sinais.PROCESSANDO=3 WHERE sinais.ID ='"+str(self.id_sinal)+"'"
			update(sql)

class comprar_digital(threading.Thread):
	
	def __init__( self, con, API, valor, par, direcao, timeframe, id_sinal, hora, data, gale):
		threading.Thread.__init__(self)
		self.valor=valor
		self.par=par
		self.direcao=direcao
		self.timeframe=timeframe
		self.API = API
		self.id_sinal=id_sinal
		self.con = con
		self.rs = rs
		self.hora = hora
		self.data= data
		self.gale = gale
		
	def run(self):
		
		sql= "UPDATE sinais SET sinais.processando=1 WHERE sinais.ID ='"+str(self.id_sinal)+"'"
		update(sql)
	   
		_,id = API.buy_digital_spot(self.par, self.valor, self.direcao, int(self.timeframe)) ## TENTA COMPRAR OPCAO DIGITAL

		if isinstance(id, int): ## CONDICAO PARA ENTRAR NA DIGITAL

			texto = '🕵️‍♂️ *SINAL MISTER OB - DIGITAL*\n\n⏰ HORA: '+self.hora+'\n🗓 DATA: '+self.data+'\n🧭 GRAFICO: '+str(self.timeframe)+'\n💲 MOEDA: '+self.par+'\n🔹 OPERACAO: '+self.direcao+'\n\n🥇 *PRIMEIRA TENTATIVA:* Sem Gale\n🥈 *SEGUNDA TENTATIVA:*\n🥉 *TERCEIRA TENTATIVA:*\n\n💸 *LUCRO*: 0\n♻️ *RESULTADO:* Aguardando...\n'
			print(texto)
			grava_log(texto)
			id_mensagem = MensagemTelegram(texto)

			while True:
				status4,lucro4 = API.check_win_digital_v2(id)

				if status4:
					if lucro4 > 0:

						sql= "UPDATE sinais SET sinais.STATUS_FINAL='GREEN', sinais.LUCRO='"+str(lucro4)+"' WHERE sinais.ID ='"+str(self.id_sinal)+"'"
						update(sql)

						texto = '🕵️‍♂️ *SINAL MISTER OB - DIGITAL*\n\n⏰ HORA: '+self.hora+'\n🗓 DATA: '+self.data+'\n🧭 GRAFICO: '+str(self.timeframe)+'\n💲 MOEDA: '+self.par+'\n🔹 OPERACAO: '+self.direcao+'\n\n🥇 *PRIMEIRA TENTATIVA:* '+ str( '✅' if lucro4 > 0 else '🚫' )+'\n🥈 *SEGUNDA TENTATIVA:*\n🥉 *TERCEIRA TENTATIVA:*\n\n💸 *LUCRO:* '+str(lucro4)+'\n♻️ *RESULTADO:* '+ str( '✅✅✅' if lucro4 > 0 else '🚫🚫🚫' )+'\n'
						
						print(texto)
						grava_log(texto)
						MensagemTelegramEd(id_mensagem,texto)

					else:

						_,id = API.buy_digital_spot(self.par, self.valor*2.2, self.direcao, int(self.timeframe))

						
						texto = '🕵️‍♂️ *SINAL MISTER OB - DIGITAL*\n\n⏰ HORA: '+self.hora+'\n🗓 DATA: '+self.data+'\n🧭 GRAFICO: '+str(self.timeframe)+'\n💲 MOEDA: '+self.par+'\n🔹 OPERACAO: '+self.direcao+'\n\n🥇 *PRIMEIRA TENTATIVA:* '+ str( '✅' if lucro4 > 0 else '🚫' )+'\n🥈 *SEGUNDA TENTATIVA:* 1 Gale\n🥉 *TERCEIRA TENTATIVA:*\n\n💸 *LUCRO*: 0\n♻️ *RESULTADO:* Aguardando...\n'
						print(texto)
						grava_log(texto)
						MensagemTelegramEd(id_mensagem,texto)

						sql= "UPDATE sinais SET sinais.GALE_1=1 WHERE sinais.ID ='"+str(self.id_sinal)+"'"
						update(sql)

						if isinstance(id, int):

							while True:

								status5,lucro5 = API.check_win_digital_v2(id)

								if status5:
									if lucro5 > 0:

										sql= "UPDATE sinais SET sinais.STATUS_FINAL='GREEN', sinais.LUCRO='"+str(lucro5-self.valor)+"' WHERE sinais.ID ='"+str(self.id_sinal)+"'"
										update(sql)

										
										texto = '🕵️‍♂️ *SINAL MISTER OB - DIGITAL*\n\n⏰ HORA: '+self.hora+'\n🗓 DATA: '+self.data+'\n🧭 GRAFICO: '+str(self.timeframe)+'\n💲 MOEDA: '+self.par+'\n🔹 OPERACAO: '+self.direcao+'\n\n🥇 *PRIMEIRA TENTATIVA:* '+ str( '✅' if lucro4 > 0 else '🚫' )+'\n🥈 *SEGUNDA TENTATIVA:* '+ str( '✅' if lucro5 > 0 else '🚫' )+'\n🥉 *TERCEIRA TENTATIVA:*\n\n💸 *LUCRO:* '+str(lucro5-self.valor)+'\n♻️ *RESULTADO:* '+ str( '✅✅✅' if lucro5 > 0 else '🚫🚫🚫' )+'\n'
										print(texto)
										grava_log(texto)
										MensagemTelegramEd(id_mensagem,texto)


									else:


										texto = '🕵️‍♂️ *SINAL MISTER OB - DIGITAL*\n\n⏰ HORA: '+self.hora+'\n🗓 DATA: '+self.data+'\n🧭 GRAFICO: '+str(self.timeframe)+'\n💲 MOEDA: '+self.par+'\n🔹 OPERACAO: '+self.direcao+'\n\n🥇 *PRIMEIRA TENTATIVA:* '+ str( '✅' if lucro4 > 0 else '🚫' )+'\n🥈 *SEGUNDA TENTATIVA:* '+ str( '✅' if lucro5 > 0 else '🚫' )+'\n🥉 *TERCEIRA TENTATIVA:*\n\n💸 *LUCRO:* '+str(lucro5-self.valor)+'\n♻️ *RESULTADO:* '+ str( '✅✅✅' if lucro5 > 0 else '🚫🚫🚫' )+'\n'

										if (self.gale==2):

											_,id = API.buy_digital_spot(self.par, self.valor*4, self.direcao, int(self.timeframe))

											texto = '🕵️‍♂️ *SINAL MISTER OB - DIGITAL*\n\n⏰ HORA: '+self.hora+'\n🗓 DATA: '+self.data+'\n🧭 GRAFICO: '+str(self.timeframe)+'\n💲 MOEDA: '+self.par+'\n🔹 OPERACAO: '+self.direcao+'\n\n🥇 *PRIMEIRA TENTATIVA:* '+ str( '✅' if lucro4 > 0 else '🚫' )+'\n🥈 *SEGUNDA TENTATIVA:* '+ str( '✅' if lucro5 > 0 else '🚫' )+'\n🥉 *TERCEIRA TENTATIVA:* 2 Gale\n\n💸 *LUCRO*: 0\n♻️ *RESULTADO:* Aguardando...\n'
											
											print(texto)
											grava_log(texto)
											MensagemTelegramEd(id_mensagem,texto)

											sql= "UPDATE sinais SET sinais.GALE_2=1 WHERE sinais.ID ='"+str(self.id_sinal)+"'"
											update(sql)

											if isinstance(id, int):

												while True:

													status6,lucro6 = API.check_win_digital_v2(id)

													if status6:
														if lucro6 > 0:

															sql= "UPDATE sinais SET sinais.STATUS_FINAL='GREEN', sinais.LUCRO='"+str(lucro6-((self.valor*2.2)+self.valor))+"' WHERE sinais.ID ='"+str(self.id_sinal)+"'"
															update(sql)

															
															texto = '🕵️‍♂️ *SINAL MISTER OB - DIGITAL*\n\n⏰ HORA: '+self.hora+'\n🗓 DATA: '+self.data+'\n🧭 GRAFICO: '+str(self.timeframe)+'\n💲 MOEDA: '+self.par+'\n🔹 OPERACAO: '+self.direcao+'\n\n🥇 *PRIMEIRA TENTATIVA:* '+ str( '✅' if lucro4 > 0 else '🚫' )+'\n🥈 *SEGUNDA TENTATIVA:* '+ str( '✅' if lucro5 > 0 else '🚫' )+'\n🥉 *TERCEIRA TENTATIVA:* '+ str( '✅' if lucro6 > 0 else '🚫' )+'\n\n💸 *LUCRO:* '+str(lucro6-((self.valor*2.2)+self.valor))+'\n♻️ *RESULTADO:* '+ str( '✅✅✅' if lucro6 > 0 else '🚫🚫🚫' )+'\n'
															print(texto)
															grava_log(texto)
															MensagemTelegramEd(id_mensagem,texto)

														else:

															sql= "UPDATE sinais SET sinais.STATUS_FINAL='RED', sinais.LUCRO='"+str(0-(self.valor+(self.valor*2.2)+(self.valor*4)))+"' WHERE sinais.ID ='"+str(self.id_sinal)+"'"
															update(sql)

														   
															texto = '🕵️‍♂️ *SINAL MISTER OB - DIGITAL*\n\n⏰ HORA: '+self.hora+'\n🗓 DATA: '+self.data+'\n🧭 GRAFICO: '+str(self.timeframe)+'\n💲 MOEDA: '+self.par+'\n🔹 OPERACAO: '+self.direcao+'\n\n🥇 *PRIMEIRA TENTATIVA:* '+ str( '✅' if lucro4 > 0 else '🚫' )+'\n🥈 *SEGUNDA TENTATIVA:* '+ str( '✅' if lucro5 > 0 else '🚫' )+'\n🥉 *TERCEIRA TENTATIVA:* '+ str( '✅' if lucro6 > 0 else '🚫' )+'\n\n💸 *LUCRO:* '+str(lucro6-((self.valor*2.2)+self.valor))+'\n♻️ *RESULTADO:* '+ str( '✅✅✅' if lucro6 > 0 else '🚫🚫🚫' )+'\n'
															print(texto)
															grava_log(texto)
															MensagemTelegramEd(id_mensagem,texto)

														break

										else:

											sql= "UPDATE sinais SET sinais.STATUS_FINAL='RED', sinais.LUCRO='"+str(0-(self.valor+(self.valor*2.2)))+"' WHERE sinais.ID ='"+str(self.id_sinal)+"'"
											update(sql)


									break

					break


			sql= "UPDATE sinais SET sinais.processando=2 WHERE sinais.ID ='"+str(self.id_sinal)+"'"
			update(sql)
			put_balanco_atual() ## APOS A OPERACAO, É VERIFICADO O BALANCO \
			resumo_apos_op()


		elif ( id != None):  

			 if ('Cannot purchase an option' in id or 'Não foi possível abrir uma negociação' in id  ):
					texto = '-----------DIGITAL----------- \n⏰ HORA: '+self.hora+'\n🗓 DATA: '+self.data+'\n🧭 GRAFICO: '+str(self.timeframe)+'\n💲 MOEDA: '+self.par+'\n🔹 OPERACAO: '+self.direcao+'\n🔸 ID SINAL: '+str(self.id_sinal)+'\n🚫ERRO AO COMPRAR = '+str(id)+'\n-----------------------------\n'
					print(texto)
					grava_log(texto)
					MensagemTelegram(texto)
					sql = sql= "UPDATE sinais SET sinais.STATUS_FINAL='FECHADA', sinais.PROCESSANDO=3 WHERE sinais.ID ='"+str(self.id_sinal)+"'"
					update(sql)
					
		elif ( id == None): 
			texto = '-----------DIGITAL----------- \n⏰ HORA: '+self.hora+'\n🗓 DATA: '+self.data+'\n🧭 GRAFICO: '+str(self.timeframe)+'\n💲 MOEDA: '+self.par+'\n🔹 OPERACAO: '+self.direcao+'\n🔸 ID SINAL: '+str(self.id_sinal)+'\n🚫ERRO AO COMPRAR = '+str(id)+'\n-----------------------------\n'
			print(texto)
			grava_log(texto)
			MensagemTelegram(texto)
			sql = sql= "UPDATE sinais SET sinais.STATUS_FINAL='FECHADA', sinais.PROCESSANDO=3 WHERE sinais.ID ='"+str(self.id_sinal)+"'"
			update(sql)

class verifica_vela(threading.Thread):
	
	def __init__( self, API,con):
		threading.Thread.__init__(self)
		self.API = API
		self.con=con
		self.rs=rs
		
	def run(self):
		MensagemTelegramEd(id_mensagem_inicial,'✅ Conectado com sucesso!\n\n✅ Verificar Vela - Thread aberta')

		while True:
		
			time.sleep(1)
			data = PegaDataAtual()
			hora = PegaHoraAtual()
		   
			# COMPARA A HORA E DATA ATUAL COM A HORA E DATA DOS SINAL NO BANCO DE DADOS
			# FUNCAO SUBTIME É PARA DIMINUIR O HORARIO EM 1HR E 1 SEG (1H HORARIO DE DIFERENCA DO EUA PARA O BRA) (1SEG É PARA O DELAY DA COMPRA)
			sql="select * from sinais where  sinais.data='" + data + "' and SUBTIME(sinais.HORA, '0:0:5')='" + hora + "' and sinais.ja_lido=0 and sinais.processando!=4"
			mycursor = self.con.cursor(buffered=True)
			mycursor.execute(sql)
			myresult = mycursor.fetchall()
			
			
			
			for x in myresult:

				
				if (DiaSemana()==5 or DiaSemana()==6):  ## verifica se é sexta feita, para concatenar OTC
					par_thread = x[3]+'-OTC'
				else:
					par_thread=x[3]

				id_sinal_thread=x[0]
				direcao_thread=x[4]
				timeframe_thread=x[5].replace("M","")
				hora_thread = x[2]
				data_thread = x[1]

				
				if(verificar_velas(par_thread,timeframe_thread,direcao_thread,self.API)=='nao_compra'):

					 sql= "UPDATE sinais SET sinais.PROCESSANDO=4 WHERE sinais.ID ='"+str(id_sinal_thread)+"'"
					 update(sql)
					 print('MOEDA:',str(par_thread),'\nHORA:',str(hora_thread),'\n* PROBLEMAS COM VELAS - NAO VAI COMPRAR','\n')
					 MensagemTelegram('💲 MOEDA: '+str(par_thread)+'\n⏰ HORA:'+str(hora_thread)+'\n➡️ PROBLEMAS COM VELAS - NAO VAI COMPRAR')

				else:
					 print('MOEDA:',str(par_thread),'\nHORA:',str(hora_thread),'\n*NAO HA PROBLEMAS COM VELAS - VAI COMPRAR','\n')
					 MensagemTelegram('💲 MOEDA: '+str(par_thread)+'\n⏰ HORA:'+str(hora_thread)+'\n➡️ NAO HA PROBLEMAS COM VELAS - VAI COMPRAR')

class verifica_tipo_entrada(threading.Thread):
	
	def __init__( self, API,con):
		threading.Thread.__init__(self)
		self.API = API
		self.con=con
		self.rs=rs
		
	def run(self):

		MensagemTelegramEd(id_mensagem_inicial,'✅ Conectado com sucesso!\n\n✅ Verificar Vela - Thread aberta\n\n✅ Entrar Sinal - Thread aberta\n\n✅ Verificar Tipo Entrada - Thread aberta')

		while True:
		
			time.sleep(1)
			data = PegaDataAtual()
			hora = PegaHoraAtual()
		   
			# COMPARA A HORA E DATA ATUAL COM A HORA E DATA DOS SINAL NO BANCO DE DADOS
			# FUNCAO SUBTIME É PARA DIMINUIR O HORARIO EM 1HR E 1 SEG (1H HORARIO DE DIFERENCA DO EUA PARA O BRA) (1SEG É PARA O DELAY DA COMPRA)
			sql="select * from sinais where  sinais.data='" + data + "' and SUBTIME(sinais.HORA, '0:0:30')='" + hora + "' and sinais.ja_lido=0 and sinais.processando!=4"
			mycursor = self.con.cursor(buffered=True)
			mycursor.execute(sql)
			myresult = mycursor.fetchall()
			

			
			for x in myresult:

				if (DiaSemana()==5 or DiaSemana()==6):  ## verifica se é sexta feita, para concatenar OTC
					par_thread = x[3]+'-OTC'
				else:
					par_thread=x[3]

				id_sinal_thread=x[0]
				direcao_thread=x[4]
				timeframe_thread=x[5].replace("M","")
				hora_thread = x[2]
				data_thread = x[1]

				print('MOEDA:',str(par_thread),'\nHORA:',str(hora_thread),'\nINICIANDO VERIFICACAO DE ENTRADA','\n')
				texto= '💲 MOEDA: '+par_thread+'\n⏰ HORA: '+hora_thread+'\n➡️ INICIANDO VERIFICACAO DE ENTRADA'
				id_mensagem = MensagemTelegram(texto)

				x = threading.Thread(target=put_tipo_entrada, args=(par_thread,hora_thread,timeframe_thread,int(id_sinal_thread),id_mensagem))
				x.start()
			   # put_tipo_entrada(par_thread,timeframe_thread,int(id_sinal_thread))             

class entrar_sinal(threading.Thread):
	
	def __init__( self, API,con):
		threading.Thread.__init__(self)
		self.API = API
		self.con=con
		self.rs=rs
		
	def run(self):

		MensagemTelegramEd(id_mensagem_inicial,'✅ Conectado com sucesso!\n\n✅ Verificar Vela - Thread aberta\n\n✅ Entrar Sinal - Thread aberta')

		while True:
	
			time.sleep(1)
			data = PegaDataAtual()
			hora = PegaHoraAtual()
		   
			# COMPARA A HORA E DATA ATUAL COM A HORA E DATA DOS SINAL NO BANCO DE DADOS
			# FUNCAO SUBTIME É PARA DIMINUIR O HORARIO EM 1HR E 1 SEG (1H HORARIO DE DIFERENCA DO EUA PARA O BRA) (1SEG É PARA O DELAY DA COMPRA)
			sql="select * from sinais where  sinais.data='" + data + "' and SUBTIME(sinais.HORA, '0:0:2')='" + hora + "' and sinais.ja_lido=0 and sinais.processando!=4"
			mycursor = self.con.cursor(buffered=True)
			mycursor.execute(sql)
			myresult = mycursor.fetchall()
			
			for x in myresult:
				
				if(get_stop_gain()==False and get_stop_loss()==False):


					if (DiaSemana()==5 or DiaSemana()==6):  ## verifica se é sexta feita, para concatenar OTC
						par_thread = x[3]+'-OTC'
					else:
						par_thread=x[3]

				
					id_sinal_thread=x[0]
					direcao_thread=x[4]
					timeframe_thread=x[5].replace("M","")
					hora_thread = x[2]
					data_thread = x[1]
					
					valor_entrada = get_valor_entrada()
					gale = get_gale()

					mycursor = mydb.cursor()
					sql= "UPDATE sinais SET sinais.JA_LIDO=1, sinais.processando=1 WHERE sinais.ID ='"+str(id_sinal_thread)+"'"
					mycursor.execute(sql)
					mydb.commit()

				   
				
					if (str(x[9]) == 'DIGITAL'):
						 thread1 = comprar_digital(con, API,valor_entrada,par_thread,direcao_thread,timeframe_thread,id_sinal_thread,hora_thread,data_thread,gale)
						 thread1.start()
					if (str(x[9]) == 'BINARIA'):
						 thread1 = comprar_binario(con, API,valor_entrada,par_thread,direcao_thread,timeframe_thread,id_sinal_thread,hora_thread,data_thread,gale)
						 thread1.start()
					if (str(x[9]) == '0'):
						 thread1 = comprar_binario(con, API,valor_entrada,par_thread,direcao_thread,timeframe_thread,id_sinal_thread,hora_thread,data_thread,gale)
						 thread1.start()
					if (str(x[9]) == 'FECHADA'):
						 print('MOEDA:',str(par_thread),'\nHORA:',str(hora_thread),'\n* PARIDADE FECHADA','\n')
						 MensagemTelegram('💲 MOEDA: '+str(par_thread)+'\n⏰ HORA:'+str(hora_thread)+'\n🔒 PARIDADE FECHADA')
						 sql = sql= "UPDATE sinais SET sinais.STATUS_FINAL='FECHADA', sinais.PROCESSANDO=3 WHERE sinais.ID ='"+str(id_sinal_thread)+"'"
						 update(sql)

					print('STOP GAIN:',get_stop_gain())
					print('STOP LOSS:',get_stop_loss())
					
					
				else:
					if(get_stop_gain()==True):
						print ('META DO DIA BATIDA, SAIR DO MERCADO')
						MensagemTelegram('💸🤑 META DO DIA BATIDA, SAIR DO MERCADO 💸🤑')
					if(get_stop_loss()==True):
						print ('PERDEU MUITO DINHEIRO, SAIR DO MERCADO')
						MensagemTelegram('😫😭 PERDEU MUITO DINHEIRO, SAIR DO MERCADO 😫😭')


			
rs = con.cursor()               
print('stop gain: ',get_stop_gain())
print('stop loss: ',get_stop_loss())
#analisar_velas_dias_anteriores()


thread1 = verifica_vela(API,con)
thread1.start()
thread2 = entrar_sinal(API,mydb)
thread2.start()
thread3 = verifica_tipo_entrada(API,con1)
thread3.start()

##--------------------------- ESCUTA BANCO DE DADOS --------------------------##        
# LOOP INFINITO QUE FICA ESCUTANDO O BD PARA QUALQUER SINAL NOVO 
