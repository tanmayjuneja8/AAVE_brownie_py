from scripts.helpful_scripts import get_account
from brownie import network, config, interface


def main():
    get_weth()


def get_weth():
    """
    Mints WETH by depositing ETH.

    We need ABI and an Address to deploy contract.
    """
    acc = get_account()
    weth = interface.IWeth(config["networks"][network.show_active()]["weth_token"])
    tx = weth.deposit({"from": acc, "value": 0.1 * (10 ** 18)})
    tx.wait(1)
    print("Recieved 0.1 WETH.")
