import numpy as np
import pandas as pd
import pickle
from pandarallel import pandarallel
import time
import random
import logging
from os import stat

# Initialize Pandarallel
pandarallel.initialize(progress_bar=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def generate_customer_profiles_table(n_customers, random_state=0):
    np.random.seed(random_state)
    customer_id_properties = []

    for customer_id in range(n_customers):
        x_customer_id = np.random.uniform(0, 100)
        y_customer_id = np.random.uniform(0, 100)
        mean_amount = np.random.uniform(5, 100)
        std_amount = mean_amount / 2
        mean_nb_tx_per_day = np.random.uniform(0, 4)

        customer_id_properties.append(
            [
                customer_id,
                x_customer_id,
                y_customer_id,
                mean_amount,
                std_amount,
                mean_nb_tx_per_day,
            ]
        )

    customer_profiles_table = pd.DataFrame(
        customer_id_properties,
        columns=[
            "CUSTOMER_ID",
            "x_customer_id",
            "y_customer_id",
            "mean_amount",
            "std_amount",
            "mean_nb_tx_per_day",
        ],
    )

    return customer_profiles_table


def generate_terminal_profiles_table(n_terminals, random_state=0):
    np.random.seed(random_state)
    terminal_id_properties = []

    for terminal_id in range(n_terminals):
        x_terminal_id = np.random.uniform(0, 100)
        y_terminal_id = np.random.uniform(0, 100)
        terminal_id_properties.append([terminal_id, x_terminal_id, y_terminal_id])

    terminal_profiles_table = pd.DataFrame(
        terminal_id_properties,
        columns=["TERMINAL_ID", "x_terminal_id", "y_terminal_id"],
    )

    return terminal_profiles_table


def get_list_terminals_within_radius(customer_profile, x_y_terminals, r):
    x_y_customer = customer_profile[["x_customer_id", "y_customer_id"]].values.astype(
        float
    )
    squared_diff_x_y = np.square(x_y_customer - x_y_terminals)
    dist_x_y = np.sqrt(np.sum(squared_diff_x_y, axis=1))
    available_terminals = list(np.where(dist_x_y < r)[0])
    return available_terminals


def generate_transactions_table(customer_profile, start_date, nb_days=10):
    customer_transactions = []
    random.seed(int(customer_profile.CUSTOMER_ID))
    np.random.seed(int(customer_profile.CUSTOMER_ID))

    for day in range(nb_days):
        nb_tx = np.random.poisson(customer_profile.mean_nb_tx_per_day)

        if nb_tx > 0:
            for _ in range(nb_tx):
                time_tx = int(np.random.normal(86400 / 2, 20000))

                if 0 < time_tx < 86400:
                    amount = np.random.normal(
                        customer_profile.mean_amount, customer_profile.std_amount
                    )

                    if amount < 0:
                        amount = np.random.uniform(0, customer_profile.mean_amount * 2)

                    amount = np.round(amount, 2)

                    if customer_profile.available_terminals:
                        terminal_id = random.choice(
                            customer_profile.available_terminals
                        )
                        customer_transactions.append(
                            [
                                time_tx + day * 86400,
                                day,
                                customer_profile.CUSTOMER_ID,
                                terminal_id,
                                amount,
                            ]
                        )

    transactions_df = pd.DataFrame(
        customer_transactions,
        columns=[
            "TX_TIME_SECONDS",
            "TX_TIME_DAYS",
            "CUSTOMER_ID",
            "TERMINAL_ID",
            "TX_AMOUNT",
        ],
    )

    if not transactions_df.empty:
        transactions_df["TX_DATETIME"] = pd.to_datetime(
            transactions_df["TX_TIME_SECONDS"], unit="s", origin=start_date
        )
        transactions_df = transactions_df[
            [
                "TX_DATETIME",
                "CUSTOMER_ID",
                "TERMINAL_ID",
                "TX_AMOUNT",
                "TX_TIME_SECONDS",
                "TX_TIME_DAYS",
            ]
        ]

    return transactions_df


days = [120, 265, 537]


def generate_dataset(dataset_selection):
    index = int(dataset_selection)
    n_customers = 5000
    n_terminals = 10000
    nb_days = days[index - 1]
    start_date = "2025-01-01 00:00:00"
    r = 5

    logging.info("Generating customer profiles table...")
    start_time = time.time()
    customer_profiles_table = generate_customer_profiles_table(
        n_customers, random_state=0
    )
    logging.info(
        f"Customer profiles table generated in {time.time() - start_time:.2f} seconds"
    )

    logging.info("Generating terminal profiles table...")
    start_time = time.time()
    terminal_profiles_table = generate_terminal_profiles_table(
        n_terminals, random_state=1
    )
    logging.info(
        f"Terminal profiles table generated in {time.time() - start_time:.2f} seconds"
    )

    logging.info("Associating terminals to customers...")
    start_time = time.time()
    x_y_terminals = terminal_profiles_table[
        ["x_terminal_id", "y_terminal_id"]
    ].values.astype(float)

    customer_profiles_table["available_terminals"] = (
        customer_profiles_table.parallel_apply(
            lambda x: get_list_terminals_within_radius(
                x, x_y_terminals=x_y_terminals, r=r
            ),
            axis=1,
        )
    )
    customer_profiles_table["nb_terminals"] = (
        customer_profiles_table.available_terminals.apply(len)
    )
    logging.info(f"Terminals associated in {time.time() - start_time:.2f} seconds")

    logging.info("Generating transactions...")
    start_time = time.time()
    transactions_df = (
        customer_profiles_table.groupby("CUSTOMER_ID")
        .parallel_apply(
            lambda x: generate_transactions_table(
                x.iloc[0], start_date, nb_days=nb_days
            )
        )
        .reset_index(drop=True)
    )
    logging.info(f"Transactions generated in {time.time() - start_time:.2f} seconds")

    transactions_df = transactions_df.sort_values("TX_DATETIME").reset_index(drop=True)
    transactions_df.reset_index(inplace=True)
    transactions_df.rename(columns={"index": "TRANSACTION_ID"}, inplace=True)

    dataset_path = f"dataset/dataset {dataset_selection}/"

    try:
        with open(f"{dataset_path}customers.pkl", "wb") as f:
            pickle.dump(customer_profiles_table, f)
        with open(f"{dataset_path}terminals.pkl", "wb") as f:
            pickle.dump(terminal_profiles_table, f)
        with open(f"{dataset_path}transactions.pkl", "wb") as f:
            pickle.dump(transactions_df, f)
    except Exception as e:
        logging.error(f"Error saving dataset: {e}")

    dataset_size_mb = (
        stat(f"{dataset_path}customers.pkl").st_size
        + stat(f"{dataset_path}terminals.pkl").st_size
        + stat(f"{dataset_path}transactions.pkl").st_size
    ) / 1_000_000
    logging.info(f"Dataset size: {dataset_size_mb:.2f} MB")
