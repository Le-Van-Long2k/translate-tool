from llama_cpp import Llama
import time

llm = Llama(
    model_path="/home/test/llama.cpp/custom-models/gemma-4-e2b-it-Q8_0.gguf",
    n_gpu_layers=-1,
    n_batch=512,
    n_ctx=2048,
    verbose=False,
)

texts = [
    "Hello, how are you?",
    "1.",
    "ooo,,...!!!???",
    "Artificial intelligence is transforming the world.",
    "I love programming.",
]
start = time.perf_counter()


res = llm.create_chat_completion(
    messages=[
        {
            "role": "system",
            "content": "You are a professional English to Vietnamese translator.",
        },
        {
            "role": "user",
            "content": f"""
Translate the following list of texts to Vietnamese.

Return the result as a JSON array of strings, in the same order.
Only output valid JSON. Do not include explanations.

Texts:
{texts}
""",
        },
    ],
    max_tokens=512,
)
end = time.perf_counter()
output_text = res["choices"][0]["message"]["content"]

# Đếm token
tokens = len(llm.tokenize(output_text.encode("utf-8")))

total_time = end - start
time_per_token = total_time / tokens if tokens > 0 else 0

print("Output:", output_text)
print("Total time:", total_time, "seconds")
print("Tokens:", tokens)
print("Time per token:", time_per_token, "seconds/token")
print("Tokens/sec:", tokens / total_time if total_time > 0 else 0)
