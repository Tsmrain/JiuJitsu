import json

transcript_path = "/home/santiago/.gemini/antigravity-ide/brain/4c94ce71-f8cd-4c1f-b21f-47c4d87cebab/.system_generated/logs/transcript_full.jsonl"

with open("docs/Documento.tex", "r") as f:
    lines = f.read().split('\n')

with open(transcript_path, 'r') as f:
    transcript_lines = f.readlines()

for line in transcript_lines:
    try:
        data = json.loads(line)
        if data.get("type") == "PLANNER_RESPONSE":
            for tool in data.get("tool_calls", []):
                args = tool.get("args", {})
                if args.get("TargetFile") == "/home/santiago/Desktop/JiuJitsu/docs/Documento.tex":
                    name = tool.get("name")
                    if data['step_index'] >= 885:
                        continue # Skip the bad edit and any subsequent
                    if name == "replace_file_content":
                        start = args["StartLine"]
                        end = args["EndLine"]
                        repl = args["ReplacementContent"].split('\n')
                        lines = lines[:start-1] + repl + lines[end:]
                    elif name == "multi_replace_file_content":
                        chunks = args.get("ReplacementChunks", [])
                        chunks.sort(key=lambda x: x["StartLine"], reverse=True)
                        for chunk in chunks:
                            start = chunk["StartLine"]
                            end = chunk["EndLine"]
                            repl = chunk["ReplacementContent"].split('\n')
                            lines = lines[:start-1] + repl + lines[end:]
    except Exception as e:
        pass

with open("docs/Documento.tex.recovered", "w") as f:
    f.write('\n'.join(lines))
