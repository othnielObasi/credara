import { HardhatUserConfig } from 'hardhat/config';
import '@nomicfoundation/hardhat-toolbox';
import 'solidity-coverage';
import * as dotenv from 'dotenv';
dotenv.config({ path: '../.env' });

const config: HardhatUserConfig = {
  solidity: {
    version: '0.8.28',
    // viaIR is required project-wide: SmartLC's hardened constructor (separate
    // verifier/dispute-resolver/pauser roles) hits "stack too deep" without it.
    settings: { optimizer: { enabled: true, runs: 200 }, viaIR: true }
  },
  networks: {
    amoy: {
      url: process.env.POLYGON_RPC_URL || 'https://rpc-amoy.polygon.technology',
      chainId: Number(process.env.POLYGON_CHAIN_ID || 80002),
      accounts: process.env.RELAYER_PRIVATE_KEY ? [process.env.RELAYER_PRIVATE_KEY] : []
    }
  },
  etherscan: {
    // Etherscan V2 API: one key works across chains (PolygonScan included),
    // no per-network apiKey object or customChains needed.
    apiKey: process.env.POLYGONSCAN_API_KEY || ''
  }
};
export default config;
