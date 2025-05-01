import os
import discord
from discord.ext import commands
from discord import app_commands  # 슬래시 명령어 지원을 위한 임포트 추가
import requests
import json
import asyncio
from dotenv import load_dotenv
import sys
from pathlib import Path

# Load from project root .env file first, then override with local .env if it exists
root_dir = Path(os.path.abspath(__file__)).parent.parent
root_env_path = os.path.join(root_dir, '.env')
local_env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')

# Load root .env first
if os.path.exists(root_env_path):
    load_dotenv(dotenv_path=root_env_path)
    print(f"Loaded environment from {root_env_path}")

# Override with local .env if it exists
if os.path.exists(local_env_path):
    load_dotenv(dotenv_path=local_env_path, override=True)
    print(f"Overridden environment from {local_env_path}")

# 환경 변수 로드
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
MCP_API = os.getenv('MCP_SERVER_URL', 'http://localhost:5601')  # Using MCP_SERVER_URL from .env
QDRANT_URL = os.getenv('QDRANT_URL', 'http://localhost:5600')
SEARXNG_URL = os.getenv('SEARXNG_URL', 'http://localhost:5578')
BOT_PREFIX = os.getenv('BOT_PREFIX', '/')

print(f"Using MCP API: {MCP_API}")
print(f"Bot prefix: {BOT_PREFIX}")

# 인텐트 설정
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=BOT_PREFIX, intents=intents)

# 슬래시 명령어를 위한 동기화 함수 추가
async def sync_commands():
    try:
        print("Syncing commands with Discord...")
        await bot.tree.sync()
        print("Command sync complete!")
    except Exception as e:
        print(f"Command sync error: {str(e)}")

@bot.event
async def on_ready():
    print(f'{bot.user} 디스코드 봇이 시작되었습니다!')
    
    # 슬래시 명령어 동기화
    await sync_commands()
    
    # Set bot status
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching, 
            name=f"/ask 명령어로 질문하기"
        )
    )

@bot.command()
async def ping(ctx):
    """Check if bot is running"""
    await ctx.send('Pong! 봇이 정상 작동 중입니다.')

@bot.command()
async def query(ctx, *, question):
    """Legacy command for basic querying"""
    try:
        async with ctx.typing():
            # MCP 서버로 질문 전송
            response = requests.post(
                f"{MCP_API}/query",
                json={"question": question}
            )
            
            if response.status_code == 200:
                answer = response.json().get("answer", "응답을 받지 못했습니다.")
                await ctx.send(f"**질문:** {question}\n**답변:** {answer}")
            else:
                await ctx.send(f"오류가 발생했습니다. 상태 코드: {response.status_code}")
    except Exception as e:
        await ctx.send(f"오류가 발생했습니다: {str(e)}")

@bot.command()
async def ask(ctx, *, question):
    """Ask a question to the AI with full agent capabilities"""
    try:
        # First, send an acknowledgement
        reply_message = await ctx.send(f"🤔 질문을 처리하고 있습니다: '{question}'")
        
        async with ctx.typing():
            # Start the response timer
            start_time = asyncio.get_event_loop().time()
            
            # Create payload for the agent
            payload = {
                "input": question, 
                "chat_history": []  # Could store chat history per user
            }
            
            # Send to agent endpoint
            response = requests.post(
                f"{MCP_API}/agent/run",
                json=payload,
                timeout=60  # Longer timeout for agent which may use tools
            )
            
            if response.status_code != 200:
                await reply_message.edit(content=f"⚠️ 에이전트 오류가 발생했습니다. 상태 코드: {response.status_code}")
                return
            
            agent_response = response.json()
            
            # Calculate response time
            elapsed = asyncio.get_event_loop().time() - start_time
            
            # Format the final answer
            answer = agent_response.get("output", "응답을 받지 못했습니다.")
            
            # Create a Discord embed for nicer formatting
            embed = discord.Embed(
                title="AI 응답",
                description=answer,
                color=discord.Color.blue()
            )
            embed.add_field(name="처리 시간", value=f"{elapsed:.2f}초", inline=True)
            embed.set_footer(text=f"질문: {question}")
            
            await reply_message.edit(content=None, embed=embed)
            
    except requests.exceptions.RequestException as e:
        await ctx.send(f"⚠️ API 통신 오류: {str(e)}")
    except Exception as e:
        await ctx.send(f"⚠️ 오류가 발생했습니다: {str(e)}")

@bot.command()
async def search(ctx, *, query):
    """Search the web using SearxNG"""
    try:
        async with ctx.typing():
            # SearxNG API로 검색 요청
            response = requests.post(
                f"{MCP_API}/search_web",
                json={"query": query}
            )
            
            if response.status_code != 200:
                await ctx.send(f"⚠️ 검색 오류가 발생했습니다. 상태 코드: {response.status_code}")
                return
            
            results = response.json()
            
            if not results:
                await ctx.send(f"**검색어:** {query}\n결과를 찾지 못했습니다.")
                return
            
            # Create embed for nicer formatting
            embed = discord.Embed(
                title=f"'{query}' 검색 결과",
                color=discord.Color.green()
            )
            
            for i, result in enumerate(results[:3]):
                title = result.get("title", "제목 없음")
                excerpt = result.get("excerpt", "내용 없음")
                url = result.get("url", "#")
                embed.add_field(
                    name=f"결과 {i+1}: {title}",
                    value=f"{excerpt[:200]}...\n[링크]({url})",
                    inline=False
                )
            
            await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"⚠️ 오류가 발생했습니다: {str(e)}")

@bot.command()
async def rag(ctx, *, query):
    """Search the document database"""
    try:
        async with ctx.typing():
            # RAG 문서 검색 요청
            response = requests.post(
                f"{MCP_API}/mcp/v1/tools/rag_search/run",
                json={"arguments": {"query": query, "limit": 3}}
            )
            
            if response.status_code != 200:
                await ctx.send(f"⚠️ 문서 검색 오류가 발생했습니다. 상태 코드: {response.status_code}")
                return
            
            results = response.json().get("results", [])
            
            if not results:
                await ctx.send(f"**검색어:** {query}\n관련 문서를 찾지 못했습니다.")
                return
            
            # Create embed for nicer formatting
            embed = discord.Embed(
                title=f"'{query}' 문서 검색 결과",
                color=discord.Color.gold()
            )
            
            for i, result in enumerate(results[:3]):
                content = result.get("content", "내용 없음")
                source = result.get("metadata", {}).get("source", "출처 미상")
                score = result.get("metadata", {}).get("score", 0)
                embed.add_field(
                    name=f"문서 {i+1} (출처: {source}, 유사도: {score:.2f})",
                    value=f"{content[:200]}...",
                    inline=False
                )
            
            await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"⚠️ 오류가 발생했습니다: {str(e)}")

@bot.command()
async def ragsearch(ctx, *, query):
    """Search and answer with RAG (Retrieval-Augmented Generation)"""
    try:
        # Send initial message
        initial_message = await ctx.send(f"🔍 '{query}' 검색 중...")
        
        async with ctx.typing():
            # Track response time
            start_time = asyncio.get_event_loop().time()
            
            # Call the RAG search endpoint
            response = requests.post(
                f"{MCP_API}/rag_search",
                json={"query": query},
                timeout=60  # Longer timeout for RAG pipeline
            )
            
            if response.status_code != 200:
                await initial_message.edit(content=f"⚠️ RAG 검색 오류가 발생했습니다. 상태 코드: {response.status_code}")
                return
            
            result = response.json()
            answer = result.get("answer", "응답을 받지 못했습니다.")
            sources = result.get("sources", [])
            
            # Calculate response time
            elapsed = asyncio.get_event_loop().time() - start_time
            
            # Create a Discord embed for nice formatting
            embed = discord.Embed(
                title=f"'{query}' 검색 결과",
                description=answer[:4000] if len(answer) > 4000 else answer,  # Discord has a 4096 character limit for embed description
                color=discord.Color.blue()
            )
            
            # Add sources as fields
            if sources:
                source_text = ""
                for i, source in enumerate(sources[:3]):  # Limit to top 3 sources
                    title = source.get("title", "제목 없음")
                    url = source.get("url", "#")
                    source_text += f"[{i+1}] [{title}]({url})\n"
                
                embed.add_field(name="참고 자료", value=source_text, inline=False)
            
            embed.add_field(name="처리 시간", value=f"{elapsed:.2f}초", inline=True)
            embed.set_footer(text="RAG (Retrieval-Augmented Generation) 기술로 처리되었습니다.")
            
            await initial_message.edit(content=None, embed=embed)
            
    except requests.exceptions.RequestException as e:
        await ctx.send(f"⚠️ API 통신 오류: {str(e)}")
    except Exception as e:
        await ctx.send(f"⚠️ 오류가 발생했습니다: {str(e)}")

@bot.command()
async def commands(ctx):
    """Show all available commands organized by category"""
    embed = discord.Embed(
        title="💬 사용 가능한 명령어",
        description=f"Discord 봇에서 사용할 수 있는 명령어 목록입니다. 모든 명령어는 `{BOT_PREFIX}` 접두사와 함께 사용합니다.",
        color=discord.Color.blue()
    )
    
    # 간단 질문 (Simple LLM queries)
    simple_commands = [
        {"name": f"{BOT_PREFIX}ask", "value": "AI에게 질문하고 답변을 받습니다. (예: `/ask 인공지능이란 무엇인가요?`)"},
        {"name": f"{BOT_PREFIX}query", "value": "기본적인 질문-답변 기능입니다. (레거시 명령어)"}
    ]
    
    # 검색 관련 명령어 (Search-related commands)
    search_commands = [
        {"name": f"{BOT_PREFIX}ragsearch", "value": "RAG 기술을 활용하여 웹을 검색하고 정보를 종합한 답변을 제공합니다. (예: `/ragsearch 2025 대한민국 대선 일정은?`)"},
        {"name": f"{BOT_PREFIX}search", "value": "SearxNG를 이용해 웹을 검색하고 결과를 보여줍니다."},
        {"name": f"{BOT_PREFIX}rag", "value": "색인된 문서 데이터베이스에서 정보를 검색합니다."}
    ]
    
    # 유틸리티 명령어 (Utility commands)
    utility_commands = [
        {"name": f"{BOT_PREFIX}ping", "value": "봇이 작동 중인지 확인합니다."},
        {"name": f"{BOT_PREFIX}commands", "value": "이 도움말 메시지를 표시합니다."},
        {"name": f"{BOT_PREFIX}help", "value": "Discord의 기본 도움말을 표시합니다."}
    ]
    
    # 간단 질문 명령어 추가
    field_value = ""
    for cmd in simple_commands:
        field_value += f"**{cmd['name']}** - {cmd['value']}\n"
    embed.add_field(name="🤖 간단 질문", value=field_value, inline=False)
    
    # 검색 관련 명령어 추가
    field_value = ""
    for cmd in search_commands:
        field_value += f"**{cmd['name']}** - {cmd['value']}\n"
    embed.add_field(name="🔍 정보 검색", value=field_value, inline=False)
    
    # 유틸리티 명령어 추가
    field_value = ""
    for cmd in utility_commands:
        field_value += f"**{cmd['name']}** - {cmd['value']}\n"
    embed.add_field(name="🛠️ 유틸리티", value=field_value, inline=False)
    
    # 사용법 예시
    usage_examples = (
        f"**간단한 질문**: `{BOT_PREFIX}ask 인공지능의 역사에 대해 설명해줘`\n"
        f"**웹 검색**: `{BOT_PREFIX}ragsearch 2025년 주요 공휴일 일정`\n"
        f"**문서 검색**: `{BOT_PREFIX}rag 프로젝트 설명서`\n"
    )
    embed.add_field(name="📝 사용 예시", value=usage_examples, inline=False)
    
    await ctx.send(embed=embed)

# 슬래시 명령어 등록
@bot.tree.command(name="ask", description="AI에게 질문하고 답변을 받습니다")
@app_commands.describe(question="AI에게 물어볼 질문")
async def slash_ask(interaction: discord.Interaction, question: str):
    """슬래시 명령어로 AI에게 질문하기 (단순 쿼리)"""
    try:
        # 처리 중임을 알림
        await interaction.response.defer(thinking=True)
        
        # 응답 시간 측정 시작
        start_time = asyncio.get_event_loop().time()
        
        # 단순 쿼리 요청 - 에이전트 대신 /query 엔드포인트 사용
        response = requests.post(
            f"{MCP_API}/query",
            json={"question": question},
            timeout=120
        )
        
        if response.status_code != 200:
            await interaction.followup.send(f"⚠️ 오류가 발생했습니다. 상태 코드: {response.status_code}")
            return
        
        result = response.json()
        answer = result.get("answer", "응답을 받지 못했습니다.")
        
        # 응답 시간 계산
        elapsed = asyncio.get_event_loop().time() - start_time
        
        # Discord 임베드 생성
        embed = discord.Embed(
            title="AI 응답",
            description=answer[:4000] if len(answer) > 4000 else answer,
            color=discord.Color.blue()
        )
        embed.add_field(name="처리 시간", value=f"{elapsed:.2f}초", inline=True)
        embed.set_footer(text=f"질문: {question}")
        
        await interaction.followup.send(embed=embed)
            
    except requests.exceptions.RequestException as e:
        await interaction.followup.send(f"⚠️ API 통신 오류: {str(e)}")
    except Exception as e:
        await interaction.followup.send(f"⚠️ 오류가 발생했습니다: {str(e)}")

@bot.tree.command(name="ragsearch", description="웹을 검색하고 정보를 종합한 답변을 받습니다")
@app_commands.describe(query="검색할 질문이나 키워드")
async def slash_ragsearch(interaction: discord.Interaction, query: str):
    """슬래시 명령어로 RAG 검색하기"""
    try:
        # 처리 중임을 알림
        await interaction.response.defer(thinking=True)
        
        # 응답 시간 측정 시작
        start_time = asyncio.get_event_loop().time()
        
        # RAG 검색 엔드포인트 호출
        response = requests.post(
            f"{MCP_API}/rag_search",
            json={"query": query},
            timeout=60  # RAG 파이프라인을 위한 타임아웃 연장
        )
        
        if response.status_code != 200:
            await interaction.followup.send(f"⚠️ RAG 검색 오류가 발생했습니다. 상태 코드: {response.status_code}")
            return
        
        result = response.json()
        answer = result.get("answer", "응답을 받지 못했습니다.")
        sources = result.get("sources", [])
        
        # 응답 시간 계산
        elapsed = asyncio.get_event_loop().time() - start_time
        
        # Discord 임베드 생성
        embed = discord.Embed(
            title=f"'{query}' 검색 결과",
            description=answer[:4000] if len(answer) > 4000 else answer,  # Discord 임베드 설명 글자 수 제한
            color=discord.Color.blue()
        )
        
        # 출처 추가
        if sources:
            source_text = ""
            for i, source in enumerate(sources[:3]):  # 상위 3개 출처로 제한
                title = source.get("title", "제목 없음")
                url = source.get("url", "#")
                source_text += f"[{i+1}] [{title}]({url})\n"
            
            embed.add_field(name="참고 자료", value=source_text, inline=False)
        
        embed.add_field(name="처리 시간", value=f"{elapsed:.2f}초", inline=True)
        embed.set_footer(text="RAG (Retrieval-Augmented Generation) 기술로 처리되었습니다.")
        
        await interaction.followup.send(embed=embed)
            
    except requests.exceptions.RequestException as e:
        await interaction.followup.send(f"⚠️ API 통신 오류: {str(e)}")
    except Exception as e:
        await interaction.followup.send(f"⚠️ 오류가 발생했습니다: {str(e)}")

@bot.tree.command(name="search", description="SearxNG를 이용해 웹을 검색합니다")
@app_commands.describe(query="검색할 키워드")
async def slash_search(interaction: discord.Interaction, query: str):
    """슬래시 명령어로 웹 검색하기"""
    try:
        # 처리 중임을 알림
        await interaction.response.defer(thinking=True)
        
        # SearxNG API로 검색 요청
        response = requests.post(
            f"{MCP_API}/search_web",
            json={"query": query}
        )
        
        if response.status_code != 200:
            await interaction.followup.send(f"⚠️ 검색 오류가 발생했습니다. 상태 코드: {response.status_code}")
            return
        
        results = response.json()
        
        if not results:
            await interaction.followup.send(f"**검색어:** {query}\n결과를 찾지 못했습니다.")
            return
        
        # Discord 임베드 생성
        embed = discord.Embed(
            title=f"'{query}' 검색 결과",
            color=discord.Color.green()
        )
        
        for i, result in enumerate(results[:3]):
            title = result.get("title", "제목 없음")
            excerpt = result.get("excerpt", "내용 없음")
            url = result.get("url", "#")
            embed.add_field(
                name=f"결과 {i+1}: {title}",
                value=f"{excerpt[:200]}...\n[링크]({url})",
                inline=False
            )
        
        await interaction.followup.send(embed=embed)
    except Exception as e:
        await interaction.followup.send(f"⚠️ 오류가 발생했습니다: {str(e)}")

@bot.tree.command(name="commands", description="사용 가능한 모든 명령어를 카테고리별로 표시합니다")
async def slash_commands(interaction: discord.Interaction):
    """슬래시 명령어로 명령어 목록 보기"""
    embed = discord.Embed(
        title="💬 사용 가능한 명령어",
        description="Discord 봇에서 사용할 수 있는 명령어 목록입니다. 슬래시 명령어(/)를 사용하여 더 편리하게 이용할 수 있습니다.",
        color=discord.Color.blue()
    )
    
    # 간단 질문 명령어
    simple_commands = [
        {"name": "/ask", "value": "AI에게 질문하고 답변을 받습니다. (예: `/ask 인공지능이란 무엇인가요?`)"}
    ]
    
    # 검색 관련 명령어
    search_commands = [
        {"name": "/ragsearch", "value": "RAG 기술을 활용하여 웹을 검색하고 정보를 종합한 답변을 제공합니다. (예: `/ragsearch 2025 대한민국 대선 일정은?`)"},
        {"name": "/search", "value": "SearxNG를 이용해 웹을 검색하고 결과를 보여줍니다."}
    ]
    
    # 유틸리티 명령어
    utility_commands = [
        {"name": "/commands", "value": "이 도움말 메시지를 표시합니다."}
    ]
    
    # 간단 질문 명령어 추가
    field_value = ""
    for cmd in simple_commands:
        field_value += f"**{cmd['name']}** - {cmd['value']}\n"
    embed.add_field(name="🤖 간단 질문", value=field_value, inline=False)
    
    # 검색 관련 명령어 추가
    field_value = ""
    for cmd in search_commands:
        field_value += f"**{cmd['name']}** - {cmd['value']}\n"
    embed.add_field(name="🔍 정보 검색", value=field_value, inline=False)
    
    # 유틸리티 명령어 추가
    field_value = ""
    for cmd in utility_commands:
        field_value += f"**{cmd['name']}** - {cmd['value']}\n"
    embed.add_field(name="🛠️ 유틸리티", value=field_value, inline=False)
    
    # 사용법 예시
    usage_examples = (
        "**간단한 질문**: `/ask 인공지능의 역사에 대해 설명해줘`\n"
        "**웹 검색**: `/ragsearch 2025년 주요 공휴일 일정`\n"
    )
    embed.add_field(name="📝 사용 예시", value=usage_examples, inline=False)
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="ping", description="봇이 정상 작동 중인지 확인합니다")
async def slash_ping(interaction: discord.Interaction):
    """슬래시 명령어로 핑 체크하기"""
    await interaction.response.send_message('Pong! 봇이 정상 작동 중입니다.')

@bot.event
async def on_command_error(ctx, error):
    """Handle command errors"""
    if isinstance(error, commands.CommandNotFound):
        await ctx.send(f"알 수 없는 명령어입니다. `{BOT_PREFIX}help`를 입력해 도움말을 확인해주세요.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"필수 인자가 누락되었습니다. `{BOT_PREFIX}help {ctx.command}`를 입력해 사용법을 확인해주세요.")
    else:
        await ctx.send(f"명령어 실행 중 오류가 발생했습니다: {str(error)}")

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)