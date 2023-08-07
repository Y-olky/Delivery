import discord
from discord.ext import commands
import json
import os
import time
from pypresence import Presence
import shutil


TOKEN = os.environ['token']
PREFIX = '???'
GUILDID = [1136140127236784208, 1132869863560450139]
allowed_ids = [1107344435538309260] 

BALANCES_FILE = 'user_balances.json'

def add_tool(name: str, price: int):
    products[name] = price

products = {
    'Auth Kit': 4,
    'Boost Bot': 5,
    'Boost Tool': 2,
    'Token Onliner': 1,
    'Token Checker': 5,
    'Token Formatter': 1,
    'Amazon StoreCard Gen': 1,
    'Vouch Restore Discord Bot': 5,
}


with open(BALANCES_FILE, 'r') as f:
  user_balances = json.load(f)

bot = commands.Bot(command_prefix=PREFIX, intents=discord.Intents.all())

def is_allowed():
    async def predicate(ctx):
        if ctx.author.id in allowed_ids:
            return True
        else:
            embed = discord.Embed(title='Permission Denied',
                                  description="You do not have permission to use this command.",
                                  color=discord.Color.red())
            await ctx.respond(embed=embed, ephemeral=True)
            return False
    return commands.check(predicate)

def get_rich_presence():
    presence = {
        "state": "Watching For Sales",
        "details": "Lumar Tools",
        "large_image": "lumar_large",
        "large_text": "Lumar Tools",
        "small_image": "lumar_small",
        "small_text": "Lumar Tools",
        "party_id": "ae488379-351d-4a4f-ad32-2b9b01c91657",
        "party_max": 5,
        "join_secret": "MTI4NzM0OjFpMmhuZToxMjMxMjM=",
        "startTimestamp": 0
    }
    return presence

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    await update_presence()

async def update_presence():
    presence = get_rich_presence()
    activity = discord.Activity(
        state=presence["state"],
        details=presence["details"],
        type=discord.ActivityType.watching,
        large_image=presence["large_image"],
        large_text=presence["large_text"],
        small_image=presence["small_image"],
        small_text=presence["small_text"],
        party={
            "id": presence["party_id"],
            "size": [1, presence["party_max"]],
        },
        timestamps={"start": presence["startTimestamp"]},
        join_secret=presence["join_secret"]
    )
    await bot.change_presence(activity=activity, status=discord.Status.idle)

def save_balances():
    with open(BALANCES_FILE, 'w') as f:
        json.dump(user_balances, f, indent=4)

@bot.slash_command(name="restock-alert", description="restock alert ig lol")
async def restockalert(ctx, product: str, stock: int, price: str, autobuy_link: str):
    embed = discord.Embed(title='**Restock Alert**')
    embed.add_field(name=' ', value=f"— Product: **{product}**\n— Stock: {stock}\n— Price: **{price}**\n— AutoBuy: [Click Here]({autobuy_link})", inline=False)
    image_url="https://i.imgur.com/tUnEi6m.png"
    embed.set_thumbnail(url=f"{image_url}")
    await ctx.send(embed=embed)
    await ctx.respond("Sent!", ephemeral=True)


@bot.slash_command(name="add-tool", description="Add a new tool to the products")
@is_allowed()
async def add_tool_command(ctx, folder: discord.Option(discord.Attachment), price: int, filename: str = None):
    try:
        tool_name = filename or os.path.splitext(os.path.basename(folder.filename))[0]

        # Check if the tool name already exists
        if tool_name in products:
            await ctx.send(f"The tool '{tool_name}' already exists.")
            return

        # Sending initial status message
        status_message = await ctx.send("Zipping and adding the tool to the data folder...")

        # Save the uploaded ZIP file to the data folder
        target_path = os.path.join("data", tool_name + ".zip")
        with open(target_path, 'wb') as f:
            f.write(await folder.read())

        # Unzip the folder
        with zipfile.ZipFile(target_path, 'r') as zip_ref:
            zip_ref.extractall(os.path.join("data", tool_name))

        # Adding the tool
        add_tool(tool_name, price)

        # Update status message
        await status_message.edit(content=f"'{tool_name}' has been added to products.")

    except Exception as e:
        await ctx.send(f"An error occurred: {str(e)}")


@bot.slash_command(name='addbalance', description='Add balance to a user', guild_ids=GUILDID)
async def add_balance(ctx, user: discord.User, amount: int):
    user_id = str(user.id)
    user_balances[user_id] = user_balances.get(user_id, 0) + amount
    save_balances()

    embed = discord.Embed(title='Balance Updated',
                          description=f"Added {amount} to {user}'s balance. New balance: ${user_balances[user_id]}",
                          color=discord.Color.green())

    await ctx.respond(embed=embed)


@bot.slash_command(name='balance', description='Check user balance', guild_ids=GUILDID)
async def balance(ctx, user: discord.User = None):
    with open(BALANCES_FILE, 'r') as f:
      user_balances = json.load(f)
    if user is None:
        user = ctx.author

    user_id = str(user.id)
    balance = user_balances.get(user_id, 0)

    embed = discord.Embed(title='User Balance',
                          description=f"{user}'s balance: ${balance}",
                          color=discord.Color.blue())

    await ctx.respond(embed=embed)


def get_available_products():
    data_folder = 'data'
    available_products = []
    for file in os.listdir(data_folder):
        if file.endswith('.zip'):
            product_name = file[:-4]
            available_products.append(product_name)
    return available_products

@is_allowed()
@bot.slash_command(name='removebalance', description='Remove balance from a user', guild_ids=GUILDID)
async def remove_balance(ctx, user: discord.User, amount: int):
    user_id = str(user.id)
    user_balance = user_balances.get(user_id, 0)
    if amount < 0:
        embed = discord.Embed(title='Invalid Amount', description="The amount to remove must be greater than or equal to 0.", color=discord.Color.red())
        await ctx.respond(embed=embed)
        return
    if user_balance < amount:
        embed = discord.Embed(title='Insufficient Balance', description=f"{user}'s balance is not enough to remove {amount}.", color=discord.Color.red())
        await ctx.respond(embed=embed)
        return
    user_balances[user_id] -= amount
    save_balances()
    embed = discord.Embed(title='Balance Updated', description=f"Removed ${amount} from {user}'s balance. New balance: ${user_balances[user_id]}", color=discord.Color.green())
    await ctx.respond(embed=embed)

@bot.slash_command(name='claim', description='Claim a product with your balance', guild_ids=GUILDID)
async def claim(ctx, product: discord.Option(choices=get_available_products())):
    user_id = str(ctx.author.id)
    user_balance = user_balances.get(user_id, 0)
    available_products = get_available_products()
    if not available_products:
        embed = discord.Embed(title='No Available Products', description="There are currently no products available for claiming.", color=discord.Color.red())
        await ctx.respond(embed=embed)
        return
    if product not in available_products:
        embed = discord.Embed(title='Invalid Product', description="Invalid product selection.", color=discord.Color.red())
        await ctx.respond(embed=embed)
        return
    product_price = products.get(product, 0)
    if user_balance < product_price:
        embed = discord.Embed(title='Insufficient Balance', description=f"You don't have enough balance to claim {product}.", color=discord.Color.red())
        await ctx.respond(embed=embed)
        return
    file_path = os.path.join('data', f'{product}.zip')
    try:
        await ctx.author.send(file=discord.File(file_path, filename=f'{product}.zip'))
    except discord.Forbidden:
        await ctx.v("Couldn't send the file. Please make sure you have DMs enabled.")
        return
    user_balances[user_id] -= product_price
    save_balances()
    embed = discord.Embed(title='Product Claimed',
                          description=f"Successfully claimed {product}. Remaining balance: ${user_balances[user_id]}",
                          color=discord.Color.green())
    await ctx.respond(embed=embed)

@bot.slash_command(name='products', description='Show all available products and their prices', guild_ids=GUILDID)
async def show_products(ctx):
    if not products:
        embed = discord.Embed(title='No Available Products',
                              description="There are currently no products available for claiming.",
                              color=discord.Color.red())

        await ctx.respond(embed=embed)
        return

    products_list = "\n".join([f"**{product}:** ${price}" for product, price in products.items()])

    embed = discord.Embed(title='Available Products',
                          description=products_list,
                          color=discord.Color.blue())

    await ctx.respond(embed=embed)

@is_allowed()
@bot.slash_command(name='giveitem', description='Give an item to a user', guild_ids=GUILDID)
async def give_item(ctx, recipient: discord.User, product: discord.Option(choices=get_available_products())):
    file_path = os.path.join('data', f'{product}.zip')

    try:
        await recipient.send(file=discord.File(file_path, filename=f'{product}.zip'))
    except discord.Forbidden:
        embed = discord.Embed(title='Failed to Give Item',
                              description=f"I couldn't send the item to {recipient}. They may have disabled DMs or blocked me.",
                              color=discord.Color.red())
        await ctx.respond(embed=embed)
        return

    embed = discord.Embed(title='Item Given',
                          description=f"Gave {product} to {recipient}.",
                          color=discord.Color.green())
    await ctx.respond(embed=embed)


if __name__ == '__main__':
    bot.run(TOKEN)