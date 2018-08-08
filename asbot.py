import requests
import urllib3
import simplejson
import json
import time
import discord
import asyncio

class Athena:

	def __init__(self,host='127.0.0.1',port=12001):
		self.url = f'http://{host}:{port}/json_rpc'
		self.headers = {'content-type':'application/json'}

	def _make_request(self,method,**kwargs):
		payload = {
			'jsonrpc':'2.0',
			'method':method,
			'params':kwargs
		}

		response = requests.post(self.url,json.dumps(payload),self.headers)
		msg = response.json()

		return msg

	def get_transaction_pool(self):
		return self._make_request('f_on_transactions_pool_json')
	
	def get_last_block_header(self):
		return self._make_request('getlastblockheader')

	def get_block_count(self):
		return self._make_request('getblockcount')

token = open('token').read()
client = discord.Client()
channel_id = open('channel').read()
channel = discord.Object(channel_id)

daemon = Athena()

present_transactions = []

async def check_transactions(pool):
	for i in pool:
		hash = i['hash']
		if hash not in present_transactions:
			present_transactions.append(hash)
			msg = "```New Transaction found: " + hash + "```"
			print(msg)
			await client.send_message(channel,msg)
	for hash in present_transactions:
		count = 0
		for i in pool:
			if hash == i['hash']:
				count = count + 1
				break
		if count == 0:
			present_transactions.remove(hash)
			print('Removed Transaction' + hash)
	return

@client.event
async def on_ready():
	print("connected")
	last_block_height = daemon.get_block_count()['result']['count']
	mineable_block = 0
	global present_transactions
	await client.send_message(channel,'```Top Block is: ' + str(last_block_height) + '```')
	while True:
		try:
			present_height = daemon.get_block_count()['result']['count']
			pool = daemon.get_transaction_pool()['result']['transactions']
			if last_block_height != present_height:
				block_msg = "```Block " + str(last_block_height) + ' is mined```'
				print(block_msg)
				await client.send_message(channel,block_msg)
				mineable_block = 0
				if not pool:
					present_transactions = []
				else:
					await check_transactions(pool)
				last_block_height = present_height
				top_block_msg = '```New Top Block is: ' + str(last_block_height) + '```'
				await client.send_message(channel,top_block_msg)
				print(top_block_msg)
				continue
			if not pool:
				mineable_block = 0
			else:
				await check_transactions(pool)
				if len(present_transactions) >= 2:
					if not mineable_block:
						mineable_block = 1
						mine_msg = '```**New Block ' + str(last_block_height) + ' is ready to be mined**```'
						print(mine_msg)
						await client.send_message(channel,mine_msg)
						
			await asyncio.sleep(5)
		except json.decoder.JSONDecodeError:
			print("JSONDecodeError Occurred")
		except simplejson.errors.JSONDecodeError:
			print("SimpleJSONDecodeError Occurred")
		except requests.exceptions.ConnectionError:
			print("ConnectionError Occurred")
		except urllib3.exceptions.ProtocolError:
			print("ProtocolError Occurred")
		except KeyError:
			print("KeyError Occured")
		except ValueError:
			print("ValueError Occurred")


client.run(token)
