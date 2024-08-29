from tools import *
from datetime import datetime, timezone
import requests
from fake_useragent import UserAgent
web3tool=Web3Tool(rpc_url='https://testnet.storyrpc.io',chain_id=1513)
web3=web3tool.web3
contracts={}
contract_base_path='./contract'
wallet_base_path='./wallet.csv'
twocaptcha_apikey='xxx'
ua= UserAgent()
def load_contract(filename:str):
    '''
    加载合约
    '''
    # 从 JSON 文件中读取钱包信息
    with open(filename, 'r') as file:
        contract_info = json.load(file)
    return contract_info
def get_contract():
    '''
    加载并实例化所有合约
    '''
    contracts_list = glob(os.path.join(contract_base_path, '*'))
    # 使用线程池来并发加载钱包
    for contract_path in contracts_list:
        contract_info=load_contract(contract_path)
        name=contract_info.get('name')
        contract_address=contract_info.get("address")
        abi=contract_info.get('abi')
        contract_address=web3.to_checksum_address(contract_address)
        contract = web3.eth.contract(address=contract_address, abi=abi)
        contracts[name]=contract

def mint_StoryNFT(private_key):
    '''
    mint StoryNFT
    '''
    sign=get_sign(private_key)
    StoryNF_func=contracts['mint_IPNFT'].functions.mintNFTGated(Web3.to_bytes( hexstr = sign['signature']),sign['hashedTwitterId'])
    # 构建交易
    account = web3.eth.account.from_key(private_key)
    address=account.address
    while True:
        try:
            
                tx_hash,status = web3tool.run_contract(StoryNF_func,address,private_key)
                if status:
                    logger.success(f'{address}-mint StoryNFT成功-Transaction-交易哈希: {tx_hash}-交易状态: {status}')
                else:
                    logger.error(f'{address}-mint StoryNFT失败-Transaction-交易哈希: {tx_hash}-交易状态: {status}')
                    time.sleep(30)
        except Exception as e:
            logger.error(f'{address}-mint StoryNFT失败-ERROR：{e}')
            time.sleep(30)
            raise ValueError(f'{address}-mint_COLNFT失败-ERROR：{e}')
def get_nonce(address):
    headers = {
        'Accept': '*/*',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Origin': 'https://mint.story.foundation',
        'Pragma': 'no-cache',
        'Referer': 'https://mint.story.foundation/',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'User-Agent': ua.chrome,
        'sec-ch-ua': '"Chromium";v="128", "Not;A=Brand";v="24", "Google Chrome";v="128"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
    }
    json_data = {
        'walletAddress':address,
    }
    response = requests.post('https://mint.story.foundation/api/wallet/nonce', headers=headers, json=json_data)
    nonce=response.json().get('nonce')
    assert nonce,f'nonce获取失败，可能被反爬！response:{response.json()}'
    return nonce
def mint_COLNFT(private_key):
    '''
    mint_COLNFT
    '''
    account = web3.eth.account.from_key(private_key)
    address=account.address
    address=web3.to_checksum_address(address)
    mint_COLNFT_func=contracts['mint_COLNFT'].functions.safeMint(address)
    # 构建交易
    try:
        tx_hash,status = web3tool.run_contract(mint_COLNFT_func,address,private_key)
        if status:
            logger.success(f'{address}-mint_COLNFT成功-Transaction-交易哈希: {tx_hash}-交易状态: {status}')
        else:
            logger.error(f'{address}-mint_COLNFT失败-Transaction-交易哈希: {tx_hash}-交易状态: {status}')
            time.sleep(30)
    except Exception as e:
        logger.error(f'{address}-mint_COLNFT失败-ERROR：{e}')
        raise ValueError(f'{address}-mint_COLNFT失败-ERROR：{e}')
def run(wallet):
    account = web3.eth.account.from_key(wallet['private_key'])
    address=account.address
    if address not in task2_log:
        try:
            mint_COLNFT(wallet['private_key'])
            task2_log_file.write(f'{address}\n')
        except Exception as e:
            pass
    else:
        pass
    time.sleep(10)
    if address not in task1_log:
        try:
            mint_StoryNFT(wallet['private_key'])
            task1_log_file.write(f'{address}\n')
        except Exception as e:
            pass
    else:
        pass
    return wallet
def from_file_list(file_list):
    res=[]
    header=[file_list.pop(0)]
    for _ in file_list:
        res.append(dict(zip(header,[_])))
    return res
def get_2captcha_turnstile_token(sitekey,pageurl):
        params = {'key': twocaptcha_apikey, 'method': 'turnstile',
                  'sitekey': sitekey,
                  'pageurl': pageurl,
                  'json': 1}
        response = requests.get(f'https://2captcha.com/in.php?', params=params).json()
        if response['status'] != 1:
            raise ValueError(response)
        task_id = response['request']
        for _ in range(60):
            response = requests.get(
                f'https://2captcha.com/res.php?key={twocaptcha_apikey}&action=get&id={task_id}&json=1').json()
            if response['status'] == 1:
                return response['request']
            else:
                time.sleep(3)
        return False
def get_nonce(address):
    headers = {
        'Accept': '*/*',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Origin': 'https://mint.story.foundation',
        'Pragma': 'no-cache',
        'Referer': 'https://mint.story.foundation/',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'User-Agent': ua.chrome,
        'sec-ch-ua': '"Chromium";v="128", "Not;A=Brand";v="24", "Google Chrome";v="128"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
    }
    json_data = {
        'walletAddress':address,
    }
    response = requests.post('https://mint.story.foundation/api/wallet/nonce', headers=headers, json=json_data)
    nonce=response.json().get('nonce')
    assert nonce,f'nonce获取失败，可能被反爬！response:{response.json()}'
    return nonce,response.cookies.get_dict()['sp_swncn']
def get_sign(private_key):
    
    account = web3.eth.account.from_key(private_key)
    address=account.address
    # 获取当前时间（UTC）
    now_utc = datetime.now(timezone.utc)

    # 格式化时间为 ISO 8601 格式
    formatted_time = now_utc.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
    nonce=get_nonce(address)
    headers = {
        'Cookie':f'sp_swncn={nonce[1]}',
        'Accept': '*/*',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Origin': 'https://mint.story.foundation',
        'Pragma': 'no-cache',
        'Referer': 'https://mint.story.foundation/',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'User-Agent':ua.chrome,
        'sec-ch-ua': '"Chromium";v="128", "Not;A=Brand";v="24", "Google Chrome";v="128"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
    }
    
    
    msg=f'mint.story.foundation wants you to sign in with your Ethereum account:\n{address}\n\nSign in with Ethereum to the app.\n\nURI: https://mint.story.foundation\nVersion: 1\nChain ID: 1513\nNonce: {nonce[0]}\nIssued At: {formatted_time}'
    json_data = {
    'challengeToken': get_2captcha_turnstile_token('0x4AAAAAAAhtXHMv3RZpIEc7','https://mint.story.foundation/'),
    'signature': web3tool.sign_msg(private_key,msg),
    'message': msg,
    'address': address,
    }
    response = requests.post('https://mint.story.foundation/api/mint/signature', headers=headers, json=json_data)
    return response.json()
if __name__=='__main__':
    get_contract()
    file_list=open(wallet_base_path,'r').read().split('\n')
    wallets=from_file_list(file_list)
    with open('./task1_log.csv','a') as task1_log_file:
        with open('./task2_log.csv','a') as task2_log_file:
            task1_log=open('./task1_log.csv','r') .read().split('\n')
            task2_log=open('./task2_log.csv','r').read().split('\n')
            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(run, wallet) for wallet in wallets]
                for future in as_completed(futures):
                    try:
                        data = future.result()
                    except Exception as e:
                        logger.error(f"Error: {e}")
