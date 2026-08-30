CREATE SCHEMA IF NOT EXISTS gold;

CREATE TABLE IF NOT EXISTS gold.dim_clients (
    client_id VARCHAR PRIMARY KEY,
    client_name VARCHAR NOT NULL,
    client_country VARCHAR,
    risk_profile VARCHAR
);

CREATE TABLE IF NOT EXISTS gold.dim_advisors (
    advisor_id VARCHAR PRIMARY KEY,
    advisor_name VARCHAR NOT NULL
);

CREATE TABLE IF NOT EXISTS gold.dim_instruments (
    instrument_id VARCHAR PRIMARY KEY,
    instrument_name VARCHAR NOT NULL UNIQUE,
    asset_class VARCHAR
);

CREATE TABLE IF NOT EXISTS gold.dim_portfolios (
    portfolio_id VARCHAR PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS gold.dim_transaction_types (
    transaction_type_id VARCHAR PRIMARY KEY,
    transaction_type_name VARCHAR NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS gold.dim_client_portfolios (
    client_id VARCHAR NOT NULL,
    portfolio_id VARCHAR NOT NULL,
    PRIMARY KEY (client_id, portfolio_id),
    FOREIGN KEY (client_id) REFERENCES gold.dim_clients(client_id),
    FOREIGN KEY (portfolio_id) REFERENCES gold.dim_portfolios(portfolio_id)
);

CREATE TABLE IF NOT EXISTS gold.dim_channels (
    channel_id INTEGER PRIMARY KEY,
    channel_name VARCHAR NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS gold.dim_source_systems (
    source_system_id INTEGER PRIMARY KEY,
    source_system_name VARCHAR NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS gold.fact_transactions (
    transaction_id VARCHAR PRIMARY KEY,
    client_id VARCHAR,
    advisor_id VARCHAR,
    instrument_id VARCHAR,
    portfolio_id VARCHAR,
    channel_id INTEGER,
    source_system_id INTEGER,
    transaction_date DATE,
    transaction_type_id VARCHAR,
    quantity DOUBLE,
    price_per_unit DOUBLE,
    currency VARCHAR CHECK (currency IN ('CHF', 'EUR', 'USD', 'GBP')),
    gross_amount DECIMAL(18, 2) CHECK (gross_amount >= 0),
    fee DECIMAL(18, 2) DEFAULT 0 CHECK (fee >= 0),
    net_amount DECIMAL(18, 2),
    transaction_year INTEGER,
    transaction_month INTEGER,
    transaction_quarter INTEGER,
    notes VARCHAR,
    is_flagged BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (client_id) REFERENCES gold.dim_clients(client_id),
    FOREIGN KEY (advisor_id) REFERENCES gold.dim_advisors(advisor_id),
    FOREIGN KEY (instrument_id) REFERENCES gold.dim_instruments(instrument_id),
    FOREIGN KEY (portfolio_id) REFERENCES gold.dim_portfolios(portfolio_id),
    FOREIGN KEY (transaction_type_id) REFERENCES gold.dim_transaction_types(transaction_type_id),
    FOREIGN KEY (channel_id) REFERENCES gold.dim_channels(channel_id),
    FOREIGN KEY (source_system_id) REFERENCES gold.dim_source_systems(source_system_id)
);

CREATE TABLE IF NOT EXISTS gold.flagged_transactions (
    transaction_id VARCHAR PRIMARY KEY,
    client_id VARCHAR,
    advisor_id VARCHAR,
    instrument_id VARCHAR,
    portfolio_id VARCHAR,
    channel_id INTEGER,
    source_system_id INTEGER,
    transaction_date DATE,
    transaction_type_id VARCHAR,
    quantity DOUBLE,
    price_per_unit DOUBLE,
    currency VARCHAR CHECK (currency IN ('CHF', 'EUR', 'USD', 'GBP')),
    gross_amount DECIMAL(18, 2) CHECK (gross_amount >= 0),
    fee DECIMAL(18, 2) DEFAULT 0 CHECK (fee >= 0),
    net_amount DECIMAL(18, 2),
    transaction_year INTEGER,
    transaction_month INTEGER,
    transaction_quarter INTEGER,
    notes VARCHAR,
    is_flagged BOOLEAN DEFAULT TRUE,
    flagged_reason VARCHAR,
    FOREIGN KEY (client_id) REFERENCES gold.dim_clients(client_id),
    FOREIGN KEY (advisor_id) REFERENCES gold.dim_advisors(advisor_id),
    FOREIGN KEY (instrument_id) REFERENCES gold.dim_instruments(instrument_id),
    FOREIGN KEY (portfolio_id) REFERENCES gold.dim_portfolios(portfolio_id),
    FOREIGN KEY (transaction_type_id) REFERENCES gold.dim_transaction_types(transaction_type_id),
    FOREIGN KEY (channel_id) REFERENCES gold.dim_channels(channel_id),
    FOREIGN KEY (source_system_id) REFERENCES gold.dim_source_systems(source_system_id)
);
