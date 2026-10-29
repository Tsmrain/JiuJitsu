#!/usr/bin/env bash
PDF="/Users/santiago/Desktop/JiuJitsu-main/Jiu-Jitsu University.pdf"
JWT=$(cat /tmp/jwt_transition_2a1.txt)

echo "=== INICIO: $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
START=$(python3 -c "import time; print(time.time())")

# POST upload
RESP=$(curl -s -X POST http://localhost:8000/api/v1/conocimiento/fuentes/archivo \
  -H "Authorization: Bearer $JWT" \
  -F "archivo=@$PDF" \
  -F "alcance=global" \
  -F "fuente_nombre=Jiu-Jitsu University (Saulo Ribeiro)")

echo "RESP: $RESP"
JOB_ID=$(echo "$RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('job_id',''))")

# Si es async, hacer polling
if [ -n "$JOB_ID" ]; then
  echo "Polling job: $JOB_ID"
  while true; do
    STATUS=$(curl -s http://localhost:8000/api/v1/conocimiento/fuentes/procesamiento/$JOB_ID \
      -H "Authorization: Bearer $JWT")
    ESTADO=$(echo "$STATUS" | python3 -c "import sys,json; print(json.load(sys.stdin).get('estado',''))")
    echo "$(date -u +%H:%M:%SZ) estado=$ESTADO  $STATUS"
    [ "$ESTADO" = "completado" ] && break
    [ "$ESTADO" = "error" ] && break
    sleep 5
  done
fi

END=$(python3 -c "import time; print(time.time())")
echo "=== FIN: $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
echo "DURACION_SEG=$(python3 -c "print($END - $START)")"

