from discord.ext import commands
import discord
import inspect
import io
import asyncio
import textwrap
import traceback
from contextlib import redirect_stdout

class _eval(commands.Cog):

	def __init__(self, bot):
		self.bot = bot

	@commands.command(name='eval')
	async def _eval(self, ctx, *, body):

		env = {
			'ctx': ctx,
			'bot': self.bot,
			'channel': ctx.channel,
			'author': ctx.author,
			'guild': ctx.guild,
			'message': ctx.message,
			'source': inspect.getsource
		}

		banned = [
			'while True',
			'eval(',
			'exec(',
			'import os',
			'from os import',
			'dotenv',
			'pathlib'
		] #good enough

		def embed(mtype: str, out: str):
			if mtype == 'Error':
				color = discord.Color.red()
			else:
				color = discord.Color.gold()
			embed = discord.Embed(
				title = mtype,
				description = out,
				color = color
			)
			return embed

		if any(substring in body for substring in banned):
			await ctx.send(embed=embed('Output', '```no```'))
			return

		def cleanup_code(content):
			"""Automatically removes code blocks from the code."""
			# remove ```py\n```
			if content.startswith('```') and content.endswith('```'):
				return '\n'.join(content.split('\n')[1:-1])

			# remove `foo`
			return content.strip('` \n')


		def get_syntax_error(e):
			if e.text is None:
				return f'```py\n{e.__class__.__name__}: {e}\n```'
			return f'```py\n{e.text}{"^":>{e.offset}}\n{e.__class__.__name__}: {e}```'

		env.update(globals())

		body = cleanup_code(body)
		stdout = io.StringIO()
		err = out = None

		to_compile = f'async def func():\n{textwrap.indent(body, "  ")}'

		try:
			exec(to_compile, env)
		except Exception as e:
			err = await ctx.send(embed=embed('Error', f'```py\n{e.__class__.__name__}: {e}\n```'))
			await ctx.message.add_reaction('\u2049')
			await asyncio.sleep(5)
			await err.delete()
			return 
		func = env['func']
		try:
			with redirect_stdout(stdout):
				ret = await func()
		except:
			value = stdout.getvalue()
			err = await ctx.send(embed=embed('Error', f'```py\n{value}{traceback.format_exc()}\n```'))
		else:
			value = stdout.getvalue()
			if ret is None:
				if value:
					if len(value) > 500:
						value = value[:499] + '\n\n    Output Clipped '
					out = await ctx.send(embed=embed('Output', f'```py\n{value}\n```'))

			else:
				bruh = value + str(ret)
				if len(bruh) > 500:
					bruh = bruh[:499] + '\n\n    Output Clipped'
				out = await ctx.send(embed=embed('Output', f'```py\n{bruh}\n```'))

		if out:
			await ctx.message.add_reaction('\u2705')  # tick
		elif err:
			await ctx.message.add_reaction('\u2049')
			await asyncio.sleep(5)
			await err.delete()  # x
		else:
			await ctx.message.add_reaction('\u2705')


def setup(bot):
	bot.add_cog(_eval(bot))