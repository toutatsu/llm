# llm
llm

## ローカルLLMのダウンロード

### ollama

[Ollama Search](https://ollama.com/search)
```sh
docker container exec -it llm-ollama-container ollama pull gpt-oss:20b
```

## CLIから呼び出し
```sh
chmod +x llm.sh && sudo ln -s $(pwd)/llm.sh /usr/local/bin/llm
```
