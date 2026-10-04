START=$(date +%s%3N)

curl -s \
  -X POST "http://localhost:8000/language/translate/v2" \
  -H "Content-Type: application/json" \
  -d '{
    "q": [
      "你好，今天过得怎么样？希望你一切都顺利。我想和你谈谈最近一直在做的一个项目。",
      "我开始这个项目，是因为我希望能够拥有一个快速、可靠的翻译系统，可以直接运行在自己的电脑上，而不需要依赖外部的云服务。这个项目的主要目标是将英语、中文、日语和韩语翻译成越南语，同时尽可能保持翻译自然、准确并且容易理解。"
    ],
    "target": "vi",
    "max_new_tokens": 512
  }'

END=$(date +%s%3N)

echo
echo "Elapsed: $((END - START)) ms"