#Wesley Pinheiro
#pinheirocfc@gmail.com

##############Bibliotecas Uteis
import requests #realizar request na URL
import json #trabalhar com JSON
from datetime import date #variavel para o CSV
from datetime import datetime #variavel para o CSV
from bs4 import BeautifulSoup #manipular o HTML
import csv #gerar csv

##############Variaveis Gerais
#PARA COMPARATIVO DE PRECO
iQTDREDES = 0 #quantidade total de Estabelecimentos analisados
iLISTA_ANALISADOS = [] #quantidade de itens ja analisados, para comparativo de preco
iTENS_RETURN_LIST = [] #total de itens do estabelecimento formatado para posterior comparativo de preco
iSUPER = [] #para posterior montagem do dict (NOME REDE, TOTAL DE ITENS MAIS BARATOS)
iDICTSUPER = {} #dict com as redes analisadas no comparativo de preco
iLISTAGERAL = [] #lista dos itens, no loop de pesquisa de itens semelhantes
#PARA CSV
iLISTAPRODUTO = [] #lista dos produtos par montagem do CSV
iDATAATUAL = datetime.now().strftime('%Y-%m-%d')
iDIR = 'C:/Users/pinheiro/Documents/extracao_ifood.csv'
#PARA USO NAS FUNCOES
iTOTALITENS = 0 #Total de itens encontrados no estabelecimento

###########Lista de Estabelecimentos
#######Informar aqui a url do estabelecimento que sera analisado
iLISTAURL = ['https://www.ifood.com.br/delivery/sao-paulo-sp/carrefour---analia-franco-jardim-analia-franco/ae9e713a-75ee-4b5e-8a08-0bec5757fec4'
,'https://www.ifood.com.br/delivery/sao-caetano-do-sul-sp/dia-supermercado---santa-paula-santa-paula/31e3c280-331c-460f-a4ff-7ac2e6c6641f'
,'https://www.ifood.com.br/delivery/sao-paulo-sp/roldao-atacadista-ipiranga-ipiranga/85cf585b-626f-404d-90b9-9645e99a9223']

#Funcao que fara o get na url e captara o JSON contendo os itens
def iGETURL(iURL):
	headers = {
				'Content-Type': 'application/json'
				}
	iRESPONSE = requests.request("GET", iURL, headers=headers, timeout=10)
	soup = BeautifulSoup(iRESPONSE.text, 'html.parser') #html completo
	iHTML = soup.find_all('script',id='__NEXT_DATA__') #apenas tag necessario (script)
	iSCRIPT = BeautifulSoup(str(iHTML), 'html.parser') #prepara o 'script' para extracao
	iRES = iSCRIPT.find('script') #variavel com a tag script
	extraiJSON(json.loads(iRES.contents[0])) #extrai apenas o conteudo da variavel 'script'

#Funcao que extrai os dados da 'Rede + Produtos' de cada estabelecimento
def extraiJSON(jRES):	
	iREDE = jRES['props']['initialState']['restaurant']['details']['name'] #nome do estabelecimento
	print("Iniciando rede:" + str(iREDE))
	iSUPER.append((iREDE,0)) #inclui na lista, para posterior comparativo de preco	
	iTOTALITENS = 0 #total de itens encontrados no estabelecimento

	#Percorre todos os departamentos
	for jDEPTO in jRES['props']['initialState']['restaurant']['menu']: 				
		iNOMEDEPTO = jDEPTO['name'] #descricao do departamento
		
		#Percorre os itens do departamento
		for jITEM in jDEPTO['itens']: #lista de produtos
			#zera variaveis
			iPRECONORMAL = "0" #preco cheio
			iPRECOOFERTA = "0" #preco caso tenha oferta
			iPRECOVIGENTE = "0" #preco vigente (se tiver oferta: prevalece o preco da oferta)			
			iDESCRICAO = jITEM['description'] #descricao do item
			
			if "unitOriginalPrice" in jITEM: # se existe esta tag significa que o produto esta em oferta
				iPRECOOFERTA = jITEM['unitPrice'] #Preco normal
				iPRECONORMAL = jITEM['unitOriginalPrice'] #preco oferta
			else:
				iPRECONORMAL = jITEM['unitPrice'] #preco normal
			iPRECOVIGENTE = jITEM['unitPrice'] #preco vigente

			#caso o produto ja nao tenha sido inserido na lista
			#visto que ele pode estar em mais de 1 departamento(exemplo: Promoções/Mais Vendidos/Bebidas)
			if (iREDE,iNOMEDEPTO,iDESCRICAO,iPRECONORMAL,iPRECOOFERTA,iPRECOVIGENTE) not in iLISTAPRODUTO:
				iLISTAPRODUTO.append((iREDE,iNOMEDEPTO,iDESCRICAO,iPRECONORMAL,iPRECOOFERTA,iPRECOVIGENTE)) #para montagem CSV
				iTENS_RETURN_LIST.append((str(iREDE) + str(iDESCRICAO),(iDESCRICAO,iPRECOVIGENTE,iREDE))) #formato para uso no 'compararMENORPRECO'

			iTOTALITENS += 1 

	print("Rede:" + str(iREDE) + " finalizada. Total de itens encontrados:" + str(iTOTALITENS))
	return (iLISTAPRODUTO,iTENS_RETURN_LIST,iSUPER)

#funcao para criar o CSV
def criaCSV(iDIR,iLISTAPRODUTO):	
	with open(iDIR, 'w', newline='') as file:    
		fieldnames = ["iREDE" , "iNOMEDEPTO", "iDESCRICAO","iPRECONORMAL", "iPRECOOFERTA","iPRECOVIGENTE"] #cabecalho
		writer = csv.DictWriter(file, delimiter='|', fieldnames=fieldnames) #separado por |(pipe)
		writer.writeheader()
		#incluindo os itens
		for iITENS in iLISTAPRODUTO: 
			writer.writerow({
				"iREDE": iITENS[0],
				"iNOMEDEPTO": iITENS[1],
				"iDESCRICAO": iITENS[2],
				"iPRECONORMAL": iITENS[3],
				"iPRECOOFERTA": iITENS[4],
				"iPRECOVIGENTE": iITENS[5]
							})

#funcao para comparar os itens semelhantes (itens que tem em todos os estabelecimentos pesquisados)
#buscando quais redes tem o menor valor praticado
def compararMENORPRECO(iTENS_RETURN_LIST,iSUPER):	
	my_dict1 = dict(iTENS_RETURN_LIST) #dicionario com os itens 
	my_dict2 = dict(iTENS_RETURN_LIST) #dicionario com os itens 
	iDICTSUPER = dict(iSUPER) #dicionario com os estabelecimentos
	
	iQTD_SEMELHANTE = 0

	#percorre o dicionario 1 lendo item-a-item
	for key in my_dict1:
		iITEM = my_dict1[key]
		
		#se o produto ainda nao foi analisado
		if iITEM[0] not in iLISTA_ANALISADOS:
			iQTDSUPER = 0 #quantidade de estabelecimento que tem o item	 	 	
			for iPROD in my_dict2: #percorre o dict2 pra saber quantas vezes tem o item
				if my_dict2[iPROD][0] == iITEM[0]:
					iLISTAGERAL.append((my_dict2[iPROD][2],my_dict2[iPROD][1])) #guarda a lista com estabelecimento/preco
					iQTDSUPER += 1
			
			#se a quantidade de estabelecimento que tem o item foi = a qtd de estabelecimentos analisados
			if iQTDSUPER == iQTDREDES:
				iCONTA = 0 #para percorrer os itens na lista
				iPADRAO1 = iLISTAGERAL[0][1] #preco inicial = primeiro resultado
				for varrePreco in iLISTAGERAL:			
					if varrePreco[1] <= iPADRAO1: #caso o preco analisado seja menor que o anterior
						iREDEMENOR = iLISTAGERAL[iCONTA] #nome do estabelecimento
						iPADRAO1 = varrePreco[1] #preco mais em conta no momento
					iCONTA += 1
				#print(iREDEMENOR)
				iDICTSUPER.update({iREDEMENOR[0]: (iDICTSUPER[iREDEMENOR[0]] + 1)})	#adiciona 1 a quantidade de itens mais barato no estabelecimento
				iQTD_SEMELHANTE = iQTD_SEMELHANTE + 1 #quantidade de itens encontrados, iguais, nas N redes analisadas
			iLISTA_ANALISADOS.append(iITEM[0]) #itens ja analisados
		iLISTAGERAL.clear

	print("Match de itens nas " + str(iQTDREDES) + " redes:" + str(iQTD_SEMELHANTE))	
	print("Mais baratos ->")
	sort_orders = sorted(iDICTSUPER.items(), key=lambda x: x[1], reverse=True) #ordena do maior para o menor
	for i in sort_orders: #printa no terminal as redes com menor preco
		print(i[0], i[1])
			
#percorre as urls dos estabelecimentos
for iURL in iLISTAURL:
	iGETURL(iURL)
	iQTDREDES += 1 #quantidade de estabelecimentos pesquisados, para uso no comparativo de preco
print("---------")

#criar o CSV com todos os estabelecimentos/itens
print("iniciando criacao do CSV")
criaCSV(iDIR,iLISTAPRODUTO)
print("---------")

#procura match dos itens, em busca de itens que tem nos 'N' estabelecimentos pesquisados
#e informa qual o estabelecimento mais barato
print("iniciando comparacao de preco")
compararMENORPRECO(iTENS_RETURN_LIST,iSUPER)
print("---------")

	