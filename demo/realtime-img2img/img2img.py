import sys
import os

sys.path.append(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
    )
)

from utils.wrapper import StreamDiffusionWrapper

import torch
import asyncio
import aiohttp
import json

from config import Args
from pydantic import BaseModel, Field
from PIL import Image
from PIL import ImageOps
import math

base_model = "stabilityai/sd-turbo"
taesd_model = "madebyollin/taesd"

default_prompt = "vast open sky in vibrant shades of blue, wispy white clouds drifting peacefully, gentle gradients and soft edges, watercolor texture with subtle bleeding and pooling, serene and airy atmosphere, minimal landscape below with hints of trees or rooftops, digital painting, dreamy and atmospheric, high-resolution artstation-style watercolor"
default_negative_prompt = "black and white, blurry, low resolution, pixelated,  pixel art, low quality, low fidelity"

# page_content = """<h1 class="text-3xl font-bold">StreamDiffusion</h1>
# <h3 class="text-xl font-bold">Image-to-Image SD-Turbo</h3>
# <p class="text-sm">
#     This demo showcases
#     <a
#     href="https://github.com/cumulo-autumn/StreamDiffusion"
#     target="_blank"
#     class="text-blue-500 underline hover:no-underline">StreamDiffusion
# </a>
# Image to Image pipeline using
#     <a
#     href="https://huggingface.co/stabilityai/sd-turbo"
#     target="_blank"
#     class="text-blue-500 underline hover:no-underline">SD-Turbo</a
#     > with a MJPEG stream server.
# </p>
# """

page_content = ""

# OpenAI API configuration - will be set via environment variable
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

async def enhance_prompt_with_gpt4o(user_prompt: str) -> str:
    """
    Enhance user prompt using GPT-4o-mini to create better SDXL prompts
    """
    if not OPENAI_API_KEY:
        print("Warning: No OpenAI API key found, using original prompt")
        return user_prompt
    
    system_prompt = """Given this topic, come up with the best SDXL prompt. Make sure to include these exact words in the prompt: watercolor, abstract, digital art.

Return ONLY the enhanced prompt, nothing else. Make it concise and optimized for SDXL image generation. Do not mention people in the prompt."""
    
    try:
        async with aiohttp.ClientSession() as session:
            headers = {
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "max_tokens": 100,
                "temperature": 0.7
            }
            
            async with session.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    enhanced_prompt = result["choices"][0]["message"]["content"].strip()
                    print(f"Original prompt: {user_prompt}")
                    print(f"Enhanced prompt: {enhanced_prompt}")
                    return enhanced_prompt
                else:
                    print(f"OpenAI API error: {response.status}")
                    return user_prompt
                    
    except Exception as e:
        print(f"Error enhancing prompt: {e}")
        return user_prompt

class Pipeline:
    class Info(BaseModel):
        name: str = "StreamDiffusion img2img"
        input_mode: str = "image"
        page_content: str = page_content

    class InputParams(BaseModel):
        prompt: str = Field(
            default_prompt,
            title="Prompt",
            field="textarea",
            id="prompt",
        )
        # negative_prompt: str = Field(
        #     default_negative_prompt,
        #     title="Negative Prompt",
        #     field="textarea",
        #     id="negative_prompt",
        # )
        width: int = Field(
            896, min=2, max=15, title="Width", disabled=True, hide=True, id="width"
        )
        height: int = Field(
            512, min=2, max=15, title="Height", disabled=True, hide=True, id="height"
        )

    def __init__(self, args: Args, device: torch.device, torch_dtype: torch.dtype):
        params = self.InputParams()
        self.stream = StreamDiffusionWrapper(
            model_id_or_path=base_model,
            use_tiny_vae=args.taesd,
            device=device,
            dtype=torch_dtype,
            t_index_list=[15, 20],
            frame_buffer_size=1,
            width=params.width,
            height=params.height,
            use_lcm_lora=False,
            output_type="pil",
            warmup=10,
            vae_id=None,
            acceleration=args.acceleration,
            mode="img2img",
            use_denoising_batch=True,
            cfg_type="none",
            use_safety_checker=args.safety_checker,
            # enable_similar_image_filter=True,
            # similar_image_filter_threshold=0.98,
            engine_dir=args.engine_dir,
        )

        self.last_prompt = default_prompt
        self.last_enhanced_prompt = default_prompt
        self.cached_prompt = ""
        self.cached_enhanced_prompt = ""
        self.stream.prepare(
            prompt=default_prompt,
            negative_prompt=default_negative_prompt,
            num_inference_steps=50,
            guidance_scale=1.2,
        )

    async def predict(self, params: "Pipeline.InputParams") -> Image.Image:
        current_prompt = params.prompt.strip()
        
        # Only enhance prompt if it has changed
        if current_prompt != self.cached_prompt:
            print(f"New prompt detected: {current_prompt}")
            enhanced_prompt = await enhance_prompt_with_gpt4o(current_prompt)
            self.cached_prompt = current_prompt
            self.cached_enhanced_prompt = enhanced_prompt
            print(f"Cached enhanced prompt: {enhanced_prompt}")
        else:
            # Use cached enhanced prompt
            enhanced_prompt = self.cached_enhanced_prompt
        
        # Use enhanced prompt for image generation
        image_tensor = self.stream.preprocess_image(params.image)
        output_image = self.stream(image=image_tensor, prompt=enhanced_prompt)

        return output_image
