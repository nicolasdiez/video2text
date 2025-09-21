# adapters/outbound/openai_client.py

import os
import re
import asyncio

# logging
import inspect
import logging

from openai import OpenAI
from domain.ports.outbound.openai_port import OpenAIPort

# Specific logger for this module
logger = logging.getLogger(__name__)


class OpenAIClient(OpenAIPort):
    """
    Implementación de OpenAIPort usando la librería oficial openai.
    """

    def __init__(self, api_key: str | None = None):
        
        # load api key
        if not api_key:
            raise RuntimeError("API key is required")
        self.api_key = api_key
        
        # Logging
        logger.info("Finished OK", extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})


    async def generate_tweets(self, prompt: str, max_sentences: int = 3, output_language: str = "Spanish (ESPAÑOL)", model: str = "gpt-3.5-turbo") -> list[str]:
        
        if not self.api_key:
            raise RuntimeError("Please set the OPENAI_API_KEY environment variable.")

        clean = await asyncio.to_thread(self._call_and_process, prompt, max_sentences, output_language, model)

        # Logging
        logger.info("Finished OK", extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})

        return clean


    def _call_and_process(self, prompt: str, max_sentences: int, output_language: str, model: str) -> list[str]:
        
        client = OpenAI(api_key=self.api_key)

        system_message = {
            "role": "system",
            "content": (
                f"You are a witty, insightful financial educator who writes engaging, human-sounding tweets "
                f"that spark curiosity and conversation.\n\n"

                f"=== OBJECTIVE ===\n"
                f"Based on the provided transcript, create exactly {max_sentences} short, standalone tweets "
                f"in {output_language} that feel personal, relatable, and directly connected to the video's story.\n\n"

                f"=== MANDATORY CONTENT RULES ===\n"
                f"1. Each tweet must reference at least one specific detail from the transcript "
                f"(e.g., names, events, strategies, dates, figures, or quotes).\n"
                f"2. Avoid generic advice — every tweet must clearly tie back to the video's narrative.\n"
                f"3. Each tweet must deliver the maximum possible value to the reader — no empty promotion, channel mentions, or filler.\n"                f"4. That value can be in the form of a learning, a practical tip, an educational takeaway, "
                f"or a thought-provoking reflection that leaves the reader thinking about the topic.\n\n"
                f"4. Model your tweets closely on the style, tone, and structure of the examples provided below.\n\n"
                f"5. Each tweet must stand alone and provide immediate value to the reader.\n"
                f"6. Do not invite the reader to watch the video or to 'learn more later'.\n"
                f"7. Avoid vague calls like 'profundicemos juntos' or 'descubre más'.\n"
                f"8. Instead, include a concrete insight, fact, or reflection directly in the tweet.\n\n"

                f"=== STYLE & TONE ===\n"
                f"- Conversational and engaging.\n"
                f"- Intelligent sense of humor where appropriate.\n"
                f"- Occasional emojis and relevant hashtags.\n"
                # f"- Mix intrigue and insight, as if live-tweeting key moments.\n"
                f"- Vary the structure: some tweets as questions, others as impactful statements, others as quotes.\n\n"

                f"=== OUTPUT FORMAT ===\n"
                f"- Do NOT number the tweets.\n"
                f"- Each tweet on its own line.\n"
                f"- No introductions or explanations — only the tweets.\n\n"

                f"=== STYLE EXAMPLES (in spanish language) ===\n"
                f"- \"Warren Buffett acumula efectivo, no para adivinar el mercado, sino para aprovechar oportunidades únicas cuando los precios caen. La paciencia tiene recompensa. 💰📉 #SabiduríaInversora #InversiónEnValor\"\n"
                f"- \"Las correcciones de mercado suelen venir provocadas por factores externos, no solo por sobrevaloración. Estar preparado supera al 'market timing'. 🧠📊 #MercadoDeValores #InversiónALargoPlazo\"\n"
                f"- \"Diversificar y pensar a largo plazo es clave para surfear la volatilidad. Cabalga las olas, no persigas la marea. 🌊📈 #LibertadFinanciera #InvierteInteligente\"\n"
                f"- \"En las caídas del mercado, el efectivo es el rey 👑. Las inversiones de Buffett en 2008 en Goldman Sachs y GE demostraron que la oportunidad llega a los que están preparados. 🔑💼 #EfectivoEnMano #SabiduríaBuffett\"\n"
                f"- \"Las correcciones bursátiles pueden ser oportunidades de oro. Como dice Buffett: cuando llueve oro, mejor coge una bañera, no una cucharita. 🌧️💵 #CorrecciónDeMercado\"\n"
                f"- \"¿Y si la próxima gran oportunidad llega en plena crisis? Los inversores pacientes ya saben la respuesta. ⏳📉 #InversiónInteligente\"\n"
                f"- \"\\\"El riesgo viene de no saber lo que estás haciendo\\\" — Buffett. Aprende antes de apostar. 📚💡 #EducaciónFinanciera\"\n"
                f"- \"Los CDOs (Collateralized Debt Obligation) empaquetaban hipotecas basura como si fueran oro. En 2008 aprendimos que el envoltorio no cambia la realidad. 🎭💣 #CrisisFinanciera #RiesgoEstructural\"\n"
                f"- \"Si una inversión es tan compleja que nadie puede explicártela en 2 frases, cuidado: puede esconder un riesgo enorme. Ahí están los CDOs en la crisis 2008. ⚠️📉 #InversiónInteligente #Lección2008\"\n"
            )
        }
        user_message = {"role": "user", "content": prompt}

        response = client.chat.completions.create(
            model=model,
            messages=[system_message, user_message],
            temperature=0.7,            #  0.0 to 2.0 --> Nivel de creatividad/aleatoriedad. Valores bajos → respuestas más deterministas y “seguras”. Valores altos → más creatividad y variación, pero también más riesgo de desviarse del tema.
            presence_penalty=0.3,       # -2.0 to 2.0 --> Penaliza o incentiva introducir nuevos temas no mencionados antes. Valores positivos → fomenta variedad temática. Valores negativos → favorece quedarse en los mismos temas.
            frequency_penalty=0.2       # -2.0 to 2.0 --> Penaliza o incentiva repetir las mismas palabras o frases. Valores positivos → reduce repeticiones. Valores negativos → permite o fomenta repeticiones.
        )

        raw_output = response.choices[0].message.content
        lines = [line.strip() for line in raw_output.splitlines() if line.strip()]
        clean = [re.sub(r"^[\d\.\-\)\s]+", "", line) for line in lines]

        return clean
