from tools import *
web3tool=Web3Tool(rpc_url='https://testnet.storyrpc.io',chain_id=1513)
web3=web3tool.web3
contracts={}
contract_base_path='./contract'
wallet_base_path='./wallet.csv'
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
    StoryNF_func=contracts['mint_IPNFT'].functions.mintNFTGated(Web3.to_bytes( hexstr = "0x"),'0x0000000000000000000000000000000000000000000000000000000000000000')
    # 构建交易
    account = web3.eth.account.from_key(private_key)
    address=account.address
    try:
        while True:
            tx_hash,status = web3tool.run_contract(StoryNF_func,address,private_key)
            if status:
                logger.success(f'{address}-mint StoryNFT成功-Transaction-交易哈希: {tx_hash}-交易状态: {status}')
            else:
                logger.error(f'{address}-mint StoryNFT失败-Transaction-交易哈希: {tx_hash}-交易状态: {status}')
                retry+=1
                time.sleep(30)
    except Exception as e:
        logger.error(f'{address}-mint StoryNFT失败-ERROR：{e}')
        raise ValueError(f'{address}-mint StoryNFT失败-ERROR：{e}')
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
        while True:
            tx_hash,status = web3tool.run_contract(mint_COLNFT_func,address,private_key)
            if status:
                logger.success(f'{address}-mint_COLNFT成功-Transaction-交易哈希: {tx_hash}-交易状态: {status}')
                break
            else:
                logger.error(f'{address}-mint_COLNFT失败-Transaction-交易哈希: {tx_hash}-交易状态: {status}')
                time.sleep(30)
    except Exception as e:
        logger.error(f'{address}-mint_COLNFT失败-ERROR：{e}')
        raise ValueError(f'{address}-mint_COLNFT失败-ERROR：{e}')
def run(wallet):
    if wallet['is_mint1']==0:
        try:
            mint_StoryNFT(wallet['private_key'])
            wallet['is_mint1']=1
        except Exception as e:
            wallet['is_mint1']=0
    else:
        pass
    time.sleep(10)
    if wallet['is_mint2']==0:
        try:
            mint_COLNFT(wallet['private_key'])
            wallet['is_mint2']=1
        except Exception as e:
            wallet['is_mint2']=0
    else:
        pass
if __name__=='__main__':
    get_contract()
    wallets=pd.read_csv(wallet_base_path).to_dict(orient='records')
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(run, wallet) for wallet in wallets]
        for future in as_completed(futures):
            try:
                data = future.result()
            except Exception as e:
                logger.error(f"Error: {e}")
    df=pd.DataFrame(wallets)
    df.to_csv(wallet_base_path,index=False)