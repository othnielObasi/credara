import { HardhatUserConfig } from 'hardhat/config';
import '@nomicfoundation/hardhat-toolbox';
import 'solidity-coverage';
import * as dotenv from 'dotenv';
dotenv.config({ path: '../.env' });

const config: HardhatUserConfig = {
  solidity: {
    version: '0.8.28',
    settings: { optimizer: { enabled: true, runs: 200 } }
  },
  networks: {
    amoy: {
      url: process.env.POLYGON_RPC_URL || 'https://rpc-amoy.polygon.technology',
      chainId: Number(process.env.POLYGON_CHAIN_ID || 80002),
      accounts: process.env.RELAYER_PRIVATE_KEY ? [process.env.RELAYER_PRIVATE_KEY] : []
    }
  }
};
export default config;
