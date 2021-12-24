from scripts.helpful_scripts import get_account


from scripts.helpful_scripts import get_account
from brownie import network, config, interface
from scripts.get_weth import get_weth
from web3 import Web3


def main():
    acc = get_account()
    erc20_address = config["networks"][network.show_active()]["weth_token"]
    # get_weth() if already not there.
    if network.show_active() in ["mainnet-fork"]:
        get_weth()
    """ We will now deposit into AAVE network. So , we again need ABI and Address for it to happen."""
    lending_pool = get_lending_pool()
    # approve the erc20 token that we are going to end out.
    # amount = float(input("Enter the amount you want to approve ERC20 token for:"))
    amt = Web3.toWei(0.1, "ether")
    approve_erc20(amt, lending_pool.address, erc20_address, acc)
    print("Depositing...")
    tx = lending_pool.deposit(erc20_address, amt, acc.address, 0, {"from": acc})
    tx.wait(1)
    print("Deposited!")
    # ... stats of account
    borrowable_eth, total_debt = get_borrowable_data(lending_pool, acc)
    print("Let's borrow!")
    # DAI in terms of ETH
    dai_eth_price = get_asset_price(
        config["networks"][network.show_active()]["dai_eth_price_feed"]
    )
    amount_of_dai_we_can_borrow = (1 / dai_eth_price) * (borrowable_eth * 0.95)
    # borrowable eth is converted to borrowable dai with 95% accuracy so that Health Factor remains above 1.
    print(f"We are going to borrow {amount_of_dai_we_can_borrow} DAI.")
    # Now we will borrow.
    dai_address = config["networks"][network.show_active()]["dai_token"]
    borrow_tx = lending_pool.borrow(
        dai_address,
        Web3.toWei(
            amount_of_dai_we_can_borrow,
            "ether",
        ),
        2,
        0,
        acc.address,
        {"from": acc},
    )
    borrow_tx.wait(1)
    print("We borrowed some DAI!")
    get_borrowable_data(lending_pool, acc)

    # Repaying
    repay_all(amt, lending_pool, acc)
    print("You just deposited, borrowed and repaid on AAVE!")


def repay_all(amount, lending_pool, account):
    approve_erc20(
        Web3.toWei(amount, "ether"),
        lending_pool,
        config["networks"][network.show_active()]["dai_token"],
        account,
    )
    repay_tx = lending_pool.repay(
        config["networks"][network.show_active()]["dai_token"],
        uint(-1),
        2,
        account.address,
        {"from": account},
    )
    repay_tx.wait(1)
    print("Repaid!")


def get_asset_price(price_feed_address):
    # ABI and Address
    dai_eth_price_feed = interface.AggregatorV3Interface(price_feed_address)
    latest_price = dai_eth_price_feed.latestRoundData()[
        1
    ]  # (price is at 1 index) we only need price here.
    converted_latest_price = Web3.fromWei(latest_price, "ether")
    print(f"The DAI/ETH price is {converted_latest_price}.")
    return float(converted_latest_price)


def get_borrowable_data(lending_pool, account):
    (
        totalCollateralETH,
        totalDebtETH,
        availableBorrowsETH,
        currentLiquidationThreshold,
        loan_to_value,
        healthFactor,
    ) = lending_pool.getUserAccountData(account.address)
    availableBorrowsETH = Web3.fromWei(availableBorrowsETH, "ether")
    totalCollateralETH = Web3.fromWei(totalCollateralETH, "ether")
    totalDebtETH = Web3.fromWei(totalDebtETH, "ether")
    print(f"You have {totalCollateralETH} worth of ETH deposited.")
    print(f"You can borrow {availableBorrowsETH} worth of ETH .")
    print(f"You have {totalDebtETH} worth of ETH borrowed.")
    return (float(availableBorrowsETH), float(totalDebtETH))


def approve_erc20(amount, spender, erc20_address, account):
    # ABI and Address needed to compile contract.
    print("Approving ERC20 token...")
    erc20 = interface.IERC20(erc20_address)
    tx = erc20.approve(spender, amount, {"from": account})
    tx.wait(1)
    print("Approved!")
    return tx


def get_lending_pool():
    """again we need ABI and Address for knowning the exact market of AAVE. We will use interface."""
    lending_pool_addresses_provider = interface.ILendingPoolAddressesProvider(
        config["networks"][network.show_active()]["lending_pool_addresses_provider"]
    )
    lending_pool_address = lending_pool_addresses_provider.getLendingPool()
    """ Now we need ABI and Address for creating lendingpool contract."""

    lending_pool = interface.ILendingPool(lending_pool_address)
    return lending_pool
