#!/bin/bash
# Rode este script na raiz do seu repositório clonado localmente
set -e

echo "Copiando CLAUDE.md e .claude/ para o repositório..."
cp CLAUDE.md M:\REPOs\olist-customer-intelligence
cp -r .claude M:\REPOs\olist-customer-intelligence

echo "Copiando preferências pessoais para o nível global (~/.claude)..."
mkdir -p ~/.claude
cp user-level-CLAUDE.md ~/.claude/CLAUDE.md

echo "Pronto. Abra o Claude Code dentro do repositório e teste com /revisar"
