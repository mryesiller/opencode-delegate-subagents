# opencode-delegate-subagents

Pahalı ana modelin token yakan işlerini (kod tarama, test, mekanik refactor, araştırma, log analizi, review) **ucuz OpenCode-native subagent**'lara devredin.

Bu repo, [`opencode-delegate-mcp`](https://github.com/mryesiller/opencode-delegate-mcp) yaklaşımının halefidir. Eski repo, Claude Code veya Codex'in `opencode run` çağırması için bir MCP sunucusuydu. Bu repo OpenCode'un kendi subagent tanımını kullanır (`.opencode/agents/*.md`, `mode: subagent`, ajan başına `model`) — MCP adımı olmadan.

English: [README.md](README.md)

## Nasıl çalışır

```
┌──────────────────────┐  subagent aracı  ┌─────────────────────────────┐
│  Ana OpenCode        │ ───────────────► │  explorer / tester /        │
│  (pahalı model)      │                  │  refactorer / researcher /  │
│                      │ ◄─────────────── │  log-analyzer / reviewer    │
└──────────────────────┘   kısa rapor     │  (ucuz model, taze bağlam)  │
                                          └─────────────────────────────┘
```

- Subagent'lar **yeni bir çocuk oturumunda** çalışır ve ana modele ham log doldurmamak için kısa bir rapor döner ([AGENTS.md](AGENTS.md)).
- Salt okunur ajanlar (`explorer`, `researcher`, `log-analyzer`, `reviewer`) için `edit` ve `shell` yasaktır.
- Yazabilen ajanlar (`tester`, `refactorer`) dosya düzenleyip komut çalıştırabilir; `git commit` / `git push` ve başka subagent başlatmak yasaktır.

## Varsayılan modeller

Kimlikler **OpenCode 2.4.2** `opencode models` kataloğu (26 Kasım 2026) ve [models.dev](https://models.dev) üzerindeki Z.AI / NVIDIA / OpenCode kayıtlarıyla doğrulandı.

| Subagent | Model | Yazar mı? | Neden |
| --- | --- | --- | --- |
| `explorer` | `opencode/mimo-v2.6-flash-free` | hayır | Ücretsiz OpenCode modeli, kod haritası için yeterli |
| `tester` | `zai-coding-plan/glm-5.3` | evet | Z.AI Coding Plan bayrak gemisi; plan kotasında sağlam coder |
| `refactorer` | `zai-coding-plan/glm-5.3` | evet | Aynı, mekanik çok dosyalı düzenlemeler için |
| `researcher` | `opencode/deepseek-v4.1-flash-free` | hayır | Ücretsiz OpenCode modeli, kaynaklı özetlerde iyi |
| `log-analyzer` | `nvidia/z-ai/glm-5.3-flash` | hayır | NVIDIA NIM, katalogda $0, uzun bağlam |
| `reviewer` | `zai-coding-plan/glm-5.3` | hayır | Flash/ücretsizden daha iyi muhakeme; Coding Plan kotasında |

Yönlendirmeyi değiştirmek için `.opencode/agents/<ad>.md` içindeki `model:` alanını düzenleyin.

`zai-coding-plan/glm-5.3` doğrulanmış Z.AI **Coding Plan** kimliğidir (models.dev ve OpenCode 2.4.2 kataloğu). `opencode auth login` ile **Z.AI Coding Plan** seçin veya `ZHIPU_API_KEY` verin (resmi env adı; `ZAI_API_KEY` yedek olarak da kabul edilir). Kullanıma göre ödenen `zai/glm-5.3` ayrı bir sağlayıcıdır. models.dev bazı anlık görüntülerinde `opencode/glm-5.3-flash-free` ve `nvidia/z-ai/glm-5.3` (flash olmayan) görünüyor; bunlar 2.4.2 `opencode models` listesinde **yoktu**, bu yüzden varsayılan değiller. Coding Plan modelleri, sağlayıcı bağlandıktan sonra `opencode models` içinde görünür.

OpenRouter, `opencode.json` içinde isteğe bağlı sağlayıcı olarak tanımlı. Bağladıktan sonra `opencode models` çalıştırıp bir ajanı OpenRouter kimliğine yönlendirebilirsiniz.

## Gereksinimler

- [OpenCode](https://opencode.ai) **2.x** önerilir (2.4.2 ile doğrulandı). OpenCode 1.19'da da subagent vardır ve `agent/` ile `agents/` klasörlerini görür; bu repo V2 frontmatter kullanır (`permissions` listesi, `temperature` / `tools` yok). Resmi tercih edilen yol: `.opencode/agents/` (çoğul).
- Kimlik bilgileri `opencode auth login` **veya** ortam değişkenleri: Coding Plan için resmi ad `ZHIPU_API_KEY` (yedek `ZAI_API_KEY`), artı `opencode.json` içindeki `{env:NVIDIA_API_KEY}` ve `{env:OPENROUTER_API_KEY}`. Gerçek anahtarları asla commit etmeyin.

## Kurulum

```bash
git clone https://github.com/mryesiller/opencode-delegate-subagents.git
cd opencode-delegate-subagents
./install.sh --project /path/to/your/repo    # veya: ./install.sh --global
```

- `--project [dir]` ajan dosyalarını `<dir>/.opencode/agents/` altına kopyalar (varsayılan) veya `--link` ile bağlar; yoksa `AGENTS.md` ekler.
- `--global` aynı işlemi `~/.config/opencode/agents/` için yapar (`~/.config/opencode/AGENTS.md` yalnızca o dosya yoksa yazılır).
- Betik idempotent'tir: aynı dosyalar atlanır, kaynak değiştiyse ajanlar güncellenir. Mevcut `opencode.json` / `opencode.jsonc` ve mevcut bir `AGENTS.md` `--force` olmadan üzerine yazılmaz.

Sonra sağlayıcıları bağlayıp OpenCode'u yeniden başlatın:

```bash
cp .env.example .env   # yerelde doldurun, commit etmeyin
# veya:
opencode auth login    # Z.AI Coding Plan seçin; gerekirse NVIDIA / OpenCode / OpenRouter
```

Ana ajana örnek: *explorer subagent ile src/ dizinini haritala.*

## Düzen

```
.opencode/agents/     OpenCode 2.x subagent tanımları
AGENTS.md             Ne zaman devredileceği, kime, rapor biçimi
opencode.json         Örnek sağlayıcı ayarı (yalnızca env değişkenleri)
.env.example          Anahtar adları, değer yok
install.sh            Proje veya global kurulum
mcp/                  Claude Code / Codex için isteğe bağlı MCP köprüsü
docs/omp-role-mapping.md   omp rollerine önerilen hizalama (uygulanmadı)
```

## Claude Code kurulumu (MCP köprüsü)

OpenCode-native subagent'lar yalnızca OpenCode içinde çalışır. Ana ajan **Claude Code** veya **Codex** ise (örneğin Mac mini'de), bakımı süren MCP köprüsünü kullanın: [`mcp/`](mcp/README.md). Köprü `opencode run` çağırır ve varsayılan model `zai-coding-plan/glm-5.3`dır. [opencode-delegate-mcp#1](https://github.com/mryesiller/opencode-delegate-mcp/pull/1) OpenCode 2.x düzeltmesini içerir. Bu sunucu API anahtarı tutmaz — önce o makinede OpenCode'u bağlayın:

```bash
opencode auth login    # "Z.AI Coding Plan" seçin
```

Sunucuyu derleyin (Node 18+):

```bash
git clone https://github.com/mryesiller/opencode-delegate-subagents.git
cd opencode-delegate-subagents/mcp
npm install
npm run build
```

Claude Code'a kaydedin (stdio, kullanıcı kapsamı). Yolu o makinedeki `mcp/dist/index.js` mutlak yoluyla değiştirin. Bu komuta API anahtarı **koymayın**:

```bash
claude mcp add --transport stdio --scope user opencode-delegate -- node /absolute/path/to/opencode-delegate-subagents/mcp/dist/index.js
```

Diskteki ayar dosyası (`~/.config/opencode-delegate/config.json`) camelCase kullanır. Dosya yoksa varsayılan zaten Coding Plan modelidir; açıkça yazmak için:

```json
{
  "defaultModel": "zai-coding-plan/glm-5.3",
  "opencodeBin": "opencode"
}
```

Claude Code'u yeniden başlatın (veya `/mcp`).

Güvenilen bir dizinde, Claude Code'dan hızlı test:

> `list_models` aracını `zai-coding-plan` sağlayıcısıyla çalıştır. Sonra `delegate_task` ile `/tmp/opencode-delegate-smoke.txt` dosyasını oluştur; içeriği `hi` olsun.

Model listesinde `zai-coding-plan/glm-5.3` görünmeli ve duman dosyası `/tmp` altında oluşmalıdır. Sonra o dosyayı silin. `delegate_task` bilinmeyen `--dir` bayrağıyla düşerse OpenCode 2.x ikilisi bu porttan eski bir sunucu kullanıyordur — bu repodan yeniden derleyin.

## Yapılandırma notları

- Bu ajan dosyalarına `temperature` veya V1 `tools` / `permission` koymayın. OpenCode 2.x bunları eski alanlar olarak belgeler; V2 alanı (`permissions`, `mode`, `model`) kullanan bir dosyada yok sayılırlar. Gerekirse örneklemeyi sağlayıcı/model üzerinde ayarlayın.
- Anahtarlar ortamda veya `opencode auth` içinde durur, git'te değil. `.gitignore` `.env` ve `.env.*` dosyalarını yok sayar, `.env.example` tutulur.
- Model-rol eşlemesi ileride `~/.omp/agent/config.yml` (omp) ile hizalanmalıdır. Bkz. [docs/omp-role-mapping.md](docs/omp-role-mapping.md). Bu repo o dosyayı okumaz.

## Lisans

MIT. [LICENSE](LICENSE).
