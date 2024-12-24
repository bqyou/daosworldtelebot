import requests
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Hardcoded token and token addresses (Replace these with actual values)
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TOKEN_ADDRESSES = '0x3e43cB385A6925986e7ea0f0dcdAEc06673d4e10,0x20ef84969f6d81Ff74AE4591c331858b20AD82CD,0x2b0772BEa2757624287ffc7feB92D03aeAE6F12D'  # Comma-separated list of token addresses

# API endpoint
API_URL = 'https://api.dexscreener.com/latest/dex/tokens/'

# Function to fetch data from the API
def fetch_market_data(token_addresses):
    url = f"{API_URL}{token_addresses}"
    response = requests.get(url)
    print("API Response:", response.json())  # Log the API response to the console
    return response.json()

# Function to format numbers into human-readable form (e.g., K, M)
def format_value(value):
    if value >= 1_000_000:
        return f"${value / 1_000_000:.2f}M"
    elif value >= 1_000:
        return f"${value / 1_000:.2f}K"
    else:
        return f"${value:.2f}"

# Function to process /price command
async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    market_caps = {}
    
    # Fetch market data for the given token addresses
    data = fetch_market_data(TOKEN_ADDRESSES)
    if 'pairs' in data:
        for pair in data['pairs']:
            if 'quoteToken' in pair and 'baseToken' in pair and 'marketCap' in pair and 'liquidity' in pair:
                ticker = pair['baseToken']['symbol']  # Use baseToken.symbol as the ticker
                token_name = pair['baseToken']['name']  # Get the token name
                market_cap = pair['marketCap']
                liquidity_usd = pair['liquidity']['usd']
                price_usd = pair['priceUsd']
                
                # If ticker already exists, check which one has the higher liquidity
                if ticker in market_caps:
                    if market_caps[ticker]['liquidity_usd'] < liquidity_usd:
                        market_caps[ticker] = {'market_cap': market_cap, 'liquidity_usd': liquidity_usd, 'price_usd': price_usd, 'token_name': token_name}
                else:
                    market_caps[ticker] = {'market_cap': market_cap, 'liquidity_usd': liquidity_usd, 'price_usd': price_usd, 'token_name': token_name}

    # Sort the market caps in descending order
    sorted_market_caps = sorted(market_caps.items(), key=lambda x: x[1]['market_cap'], reverse=True)

    # Format the response
    formatted_response = ""
    for ticker, values in sorted_market_caps:
        token_name = values['token_name']
        market_cap_formatted = format_value(values['market_cap'])
        liquidity_formatted = format_value(values['liquidity_usd'])
        price_formatted = f"💰 {values['price_usd']}" if values['price_usd'] else "💰 N/A"
        
        formatted_response += f"{token_name} ({ticker})\n{price_formatted}\n💎 MC: {market_cap_formatted}\n💧 Liq: {liquidity_formatted}\n\n"

    # Send the response back to the user
    await update.message.reply_text(formatted_response)

# Main function to run the bot
def main():
    # Set up the Telegram bot
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Add the /price command handler
    application.add_handler(CommandHandler('price', price))

    # Start the bot
    application.run_polling()

if __name__ == '__main__':
    main()
