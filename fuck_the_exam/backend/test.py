curl -X POST \
  "https://generativelanguage.googleapis.com/v1beta2/models/gemini-3-flash-preview:generateContent?key=AIzaSyAqhZnrmN9L314qr99kBVUb7kNEpYsTb8M" \
  -H "Content-Type: application/json" \
  -d '{
    "contents": [
      {
        "parts": [
          {"text": "请写一段日语问候语"}
        ]
      }
    ]
  }'