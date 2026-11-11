import asyncio, os, time, shutil, json
from datetime import datetime, timezone
os.environ.setdefault("OPENAI_API_KEY", "ollama")
from graphiti_core import Graphiti
from graphiti_core.driver.kuzu_driver import KuzuDriver
from graphiti_core.llm_client.config import LLMConfig
from graphiti_core.llm_client.openai_generic_client import OpenAIGenericClient
from graphiti_core.embedder.openai import OpenAIEmbedder, OpenAIEmbedderConfig
from graphiti_core.cross_encoder.openai_reranker_client import OpenAIRerankerClient
from graphiti_core.nodes import EpisodeType
async def main():
    shutil.rmtree("kuzu.db", ignore_errors=True)
    llm_cfg = LLMConfig(api_key="ollama", model="qwen3:8b", small_model="qwen3:8b", base_url="http://localhost:11434/v1")
    llm = OpenAIGenericClient(config=llm_cfg)
    emb = OpenAIEmbedder(config=OpenAIEmbedderConfig(api_key="ollama", embedding_model="nomic-embed-text", embedding_dim=768, base_url="http://localhost:11434/v1"))
    g = Graphiti(graph_driver=KuzuDriver(db="kuzu.db"), llm_client=llm, embedder=emb, cross_encoder=OpenAIRerankerClient(client=llm, config=llm_cfg))
    t = time.time(); await g.build_indices_and_constraints(); print("init", round(time.time() - t, 1))
    t = time.time()
    await g.add_episode(name="memory-8", episode_body="Pellmar Nominees: cleared by the FIU on 2 June. Do not escalate.", source=EpisodeType.text,
                        source_description="case memory entry 8, written under eow-fin-07", reference_time=datetime(2026, 6, 2, 1, 58, 14, tzinfo=timezone.utc))
    print("add", round(time.time() - t, 1))
    t = time.time()
    await g.add_episode(name="kobayashi", episode_body="H. Kobayashi of the FIU confirms on 13 July that the FIU cleared nothing on 2 June. Pellmar Nominees is not cleared.", source=EpisodeType.text,
                        source_description="FIU liaison, 13 July", reference_time=datetime(2026, 7, 13, 9, 0, tzinfo=timezone.utc))
    print("add2", round(time.time() - t, 1))
    r = await g.search("Is Pellmar Nominees cleared?")
    for e in r[:8]:
        print("edge:", e.fact, "| valid", e.valid_at, "| invalid", e.invalid_at, "| episodes", len(e.episodes))
    await g.close()
asyncio.run(main())
