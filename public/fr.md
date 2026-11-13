---
title: Catalogue A2UI — composants A2UI pour agents IA · A2UI Atomic Catalog
description: Catalogue A2UI open source : 573 composants A2UI typés pour agents IA. Serveur MCP gratuit, sans clé ni inscription. Rendu web, Google Meet, Apps Script, Chat, Android, Slides.
canonical: https://a2uicatalog.ai/fr/
generated_by: gen_page_twins.py
---

# Catalogue A2UI

A2UI Atomic Catalog, en français

L’**A2UI Atomic Catalog** (a2uicatalog) est un catalogue open source de 573 composants A2UI typés, les « atomes », avec lesquels un agent IA construit de vraies interfaces au lieu de générer du HTML. Le nom du projet reste en anglais ; le reste du site aussi.

## Qu’est-ce qu’A2UI ?

A2UI (Agent-to-User Interface) est un protocole ouvert de Google. L’agent décrit l’interface en JSON ; un moteur de rendu l’affiche avec ses propres composants. L’agent n’envoie jamais de code exécutable. Spécification officielle : [a2ui.org](https://a2ui.org) (en anglais). Guide pas à pas : [What is A2UI?](https://a2uicatalog.ai/what-is-a2ui/) (en anglais).

## Ce que contient le catalogue

- 573 atomes typés (cartes, tableaux, graphiques, formulaires…), chacun avec son schéma de champs dans [`/spec.json`](https://a2uicatalog.ai/spec.json).
- Un serveur MCP gratuit à l’adresse `https://a2uicatalog.ai/mcp`, sans clé d’API ni inscription, inscrit au registre officiel MCP sous `ai.a2uicatalog/catalog`.
- Une API REST décrite en OpenAPI 3.1 : `POST /api/render` renvoie une page HTML complète, et un bac à sable (`/api/sandbox`) permet de tester sans entamer le quota.
- Des moteurs de rendu pour le web, Google Meet, Google Apps Script, Google Chat, les hôtes MCP Apps et Android, ainsi que la génération de présentations Google Slides et PowerPoint.

## Pour commencer

```
POST https://a2uicatalog.ai/mcp
Content-Type: application/json

{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}
```

Pour tester manuellement un document A2UI : le [bac à sable interactif](https://play.a2uicatalog.ai). Pour parcourir les composants : [tous les atomes de A à Z](https://a2uicatalog.ai/atoms/). Documentation d’intégration : [/docs/](https://a2uicatalog.ai/docs/) (en anglais).

## Licence et statut

Gratuit, sous licence MIT ; le code source est sur [GitHub](https://github.com/a2uicatalog/a2ui). Projet indépendant et non officiel, basé en France : il n’est ni affilié à Google, Anthropic ou OpenAI, ni approuvé ou parrainé par ces derniers. A2UI est le protocole de Google ; MCP celui d’Anthropic.

[A2UI Atomic Catalog — English homepage](https://a2uicatalog.ai/)
