#!/usr/bin/env bash
# sync.sh — Sincroniza /tmp/rev/ → diretório local do usuário
# Uso: bash sync.sh /caminho/para/reverseaffinity
#
# Copia todos os arquivos modificados, preserva estrutura,
# e mantém backup dos arquivos antigos.

set -euo pipefail

SRC="/tmp/rev"
DST="${1:-$HOME/Downloads/reverseaffinity-main}"

if [ ! -d "$SRC" ]; then
    echo "Erro: diretório fonte $SRC não encontrado"
    exit 1
fi

if [ ! -d "$DST" ]; then
    echo "Aviso: diretório destino $DST não existe"
    read -p "Criar? [y/N] " yn
    if [ "$yn" != "y" ]; then exit 1; fi
    mkdir -p "$DST"
fi

echo "Sincronizando $SRC → $DST"
echo

# Backup dos arquivos existentes
BACKUP="${DST}.bak.$(date +%s)"
echo "→ Backup em $BACKUP"
cp -r "$DST" "$BACKUP" 2>/dev/null || true

# Copia tudo, exceto __pycache__, .git, etc.
rsync -av --delete \
    --exclude='__pycache__/' \
    --exclude='*.pyc' \
    --exclude='.git/' \
    --exclude='.gitignore' \
    --exclude='*.bak*' \
    "$SRC/" "$DST/"

echo
echo "✓ Sincronização concluída!"
echo
echo "Para executar:"
echo "  cd $DST"
echo "  python3 main.py          # Home launcher"
echo "  python3 main.py photo    # Photo editor"
echo "  python3 main.py video    # Video editor"
echo "  python3 main.py effects  # Effects"
echo "  python3 main.py help     # Ajuda"
