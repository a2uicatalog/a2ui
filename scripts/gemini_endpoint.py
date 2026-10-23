"""gemini_endpoint.py - one config string names the Gemini endpoint the tests call. Nothing about a
deployment is written in code: the project, region, model and key all come from the string.

    type=gemini-enterprise;project=<number or id>;region=<region>;model=<model>[;account=<gcloud account>]
        Gemini Enterprise: the Vertex AI generateContent endpoint the app's AI Config builds from the same three
        answers (project number or ID, region, model), with a bearer token as for vertex
    type=vertex;project=<number or id>;region=global;model=<model>[;account=<gcloud account>]
        Vertex AI with a bearer token from `gcloud auth print-access-token` (or token_env=<VAR>)
    type=vertex-express;model=<model>;key_env=<VAR>
        Vertex AI Express Mode, API key
    type=ai-studio;model=<model>;key_env=<VAR>
        Gemini API (generativelanguage.googleapis.com), API key
    type=url;url=<full generateContent URL>;model=<model>[;key_env=<VAR> | ;account=<gcloud account>]
        any other endpoint taking the same request shape

thinking=low|high (Gemini 3 thinking level) or thinking=<token budget> asks the model to think less or more. Not set,
the model decides, which is what the app does. Replies at each setting are cached apart (cache/<model>@thinking-low/).

Any value written as $NAME is read from that environment variable, so one string serves every deployment:
    type=gemini-enterprise;project=$GE_PROJECT;region=$GE_REGION;model=gemini-3.8-flash

key=<value> also works, but key_env keeps the key out of shell history and CI logs. Fields are split
on ';' and each on its first '=', so a URL may carry its own query string.

Replies are cached under gemini-rig/cache/<model>/<sha of prompt>.json, so a test run replays them
for free and an endpoint change for the same model reuses them.
"""
import hashlib, json, os, re, subprocess, time, urllib.error, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, 'cache')
TYPES = ('gemini-enterprise', 'vertex', 'vertex-express', 'ai-studio', 'url')


GE_URL = re.compile(r'^https://(?:([a-z]+-[a-z]+\d+)-aiplatform\.googleapis\.com|aiplatform\.(eu|us)\.rep\.googleapis\.com|aiplatform\.googleapis\.com)'
                    r'/v1/projects/([^/]+)/locations/([^/]+)/publishers/google/models/([^/:]+):generateContent$')


def host_for(region):
    """As the app's AI Config builds it: eu and us are multi-regions on their own host."""
    if region == 'global':
        return 'aiplatform.googleapis.com'
    if region in ('eu', 'us'):
        return 'aiplatform.%s.rep.googleapis.com' % region
    return region + '-aiplatform.googleapis.com'


def parse(config):
    config = (config or '').strip()
    if config.startswith('https://'):
        # a pasted endpoint URL, as the app's AI Config takes it: a Gemini Enterprise URL is read back into its
        # project, region and model (ui.js parseVertexEndpoint); any other URL is used as it is
        m = GE_URL.match(config.split(';')[0])
        rest = config.split(';', 1)[1] if ';' in config else ''
        if m and (m.group(1) or m.group(2) or 'global') == m.group(4):
            config = 'type=gemini-enterprise;project=%s;region=%s;model=%s;%s' % (m.group(3), m.group(4), m.group(5), rest)
        else:
            config = 'type=url;url=%s;model=%s;%s' % (config.split(';')[0], config.split('/models/')[-1].split(':')[0] if '/models/' in config else 'custom', rest)
    cfg = {}
    for part in (config or '').split(';'):
        part = part.strip()
        if not part:
            continue
        if '=' not in part:
            raise ValueError('config field %r has no "=" (expected key=value; key=value)' % part)
        k, v = part.split('=', 1)
        v = v.strip()
        if v.startswith('$'):
            if not os.environ.get(v[1:]):
                raise ValueError('%s=%s: environment variable %s is not set' % (k.strip(), v, v[1:]))
            v = os.environ[v[1:]]
        cfg[k.strip()] = v
    if cfg.get('thinking') and not (cfg['thinking'].isdigit() or cfg['thinking'] in ('low', 'high')):
        raise ValueError('thinking: low, high, or a token budget such as 2048')
    t = cfg.get('type')
    if t not in TYPES:
        raise ValueError('config type must be one of %s, got %r' % (', '.join(TYPES), t))
    if not cfg.get('model'):
        raise ValueError('config needs model=<model>')
    if t in ('vertex', 'gemini-enterprise'):
        # the same checks as the app's AI Config (ui.js vertexEndpoint)
        if not re.match(r'^(?:\d{6,20}|[a-z][a-z0-9-]{4,28}[a-z0-9])$', cfg.get('project', '')):
            raise ValueError('type=%s needs project=<project number (digits) or project ID>' % t)
        # no default: the deployment names its own region, as it names its project
        if not re.match(r'^(?:global|eu|us|[a-z]+-[a-z]+\d+)$', cfg.get('region', '').lower()):
            raise ValueError('type=%s needs region=<"global", the "eu" or "us" multi-region, or a region such as europe-west4>' % t)
        cfg['region'] = cfg['region'].lower()
    if t == 'url' and not cfg.get('url', '').startswith('https://'):
        raise ValueError('type=url needs url=https://...')
    if t in ('vertex-express', 'ai-studio') and not _key(cfg):
        raise ValueError('type=%s needs key_env=<VAR> (set in the environment) or key=<value>' % t)
    return cfg


def _key(cfg):
    if cfg.get('key_env'):
        return os.environ.get(cfg['key_env'], '')
    return cfg.get('key', '')


_TOKENS, _TOKEN_LOCK = {}, __import__('threading').Lock()
TOKEN_REUSE_S = 45 * 60   # a gcloud access token lasts an hour; fetch a fresh one well before that


def _token(cfg):
    """The bearer token for a Gemini Enterprise / Vertex call: from token_env, else `gcloud auth print-access-token`
    for the named account, reused for 45 minutes rather than fetched before every call."""
    if cfg.get('token_env'):
        return os.environ.get(cfg['token_env'], '')
    acct = cfg.get('account', '')
    with _TOKEN_LOCK:
        tok, at = _TOKENS.get(acct, ('', 0))
        if tok and time.time() - at < TOKEN_REUSE_S:
            return tok
        cmd = ['gcloud', 'auth', 'print-access-token'] + (['--account=' + acct] if acct else [])
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode or not r.stdout.strip():
            raise RuntimeError('no gcloud token (run `gcloud auth login%s` in a terminal): %s' % (' ' + acct if acct else '', r.stderr.strip()[:200]))
        _TOKENS[acct] = (r.stdout.strip(), time.time())
        return _TOKENS[acct][0]


def describe(cfg):
    """The endpoint without any secret, for test output."""
    return ';'.join('%s=%s' % (k, '***' if k in ('key', 'token') else v) for k, v in cfg.items())


def request(cfg):
    """(url, headers) for one generateContent call."""
    t, m = cfg['type'], cfg['model']
    if t in ('vertex', 'gemini-enterprise'):
        region = cfg['region']
        host = host_for(region)
        url = 'https://%s/v1/projects/%s/locations/%s/publishers/google/models/%s:generateContent' % (host, cfg['project'], region, m)
        return url, {'Authorization': 'Bearer ' + _token(cfg)}
    if t == 'vertex-express':
        return 'https://aiplatform.googleapis.com/v1beta1/publishers/google/models/%s:generateContent' % m, {'x-goog-api-key': _key(cfg)}
    if t == 'ai-studio':
        return 'https://generativelanguage.googleapis.com/v1beta/models/%s:generateContent' % m, {'x-goog-api-key': _key(cfg)}
    return cfg['url'], ({'x-goog-api-key': _key(cfg)} if _key(cfg) else {'Authorization': 'Bearer ' + _token(cfg)})


def cache_key(cfg):
    """The cache folder: the model, plus the thinking setting when one is asked for."""
    return cfg['model'] + ('@thinking-' + cfg['thinking'] if cfg.get('thinking') else '')


def cache_path(model, prompt):
    return os.path.join(CACHE, model, hashlib.sha256(prompt.encode()).hexdigest()[:24] + '.json')


def cached(model, prompt):
    p = cache_path(model, prompt)
    return json.load(open(p))['reply'] if os.path.exists(p) else None


def call(cfg, prompt, max_tokens=65536):
    """The reply text: from the cache, or live from the configured endpoint (then cached)."""
    return call_full(cfg, prompt, max_tokens)['reply']


def call_full(cfg, prompt, max_tokens=65536, live=True):
    """{reply, usage, finish, cached}: usage is Gemini's usageMetadata (prompt, answer and thinking tokens),
    kept in the cache so a replayed reply still reports what it cost. live=False never calls the endpoint."""
    p = cache_path(cache_key(cfg), prompt)
    if os.path.exists(p):
        d = json.load(open(p))
        return {'reply': d['reply'], 'usage': d.get('usage') or {}, 'finish': d.get('finish'), 'cached': True}
    if not live:
        return None
    url, headers = request(cfg)
    gen = {'temperature': 0.2, 'maxOutputTokens': max_tokens}
    if cfg.get('thinking'):
        t = cfg['thinking']
        gen['thinkingConfig'] = {'thinkingBudget': int(t)} if t.isdigit() else {'thinkingLevel': t}
    body = {'contents': [{'role': 'user', 'parts': [{'text': prompt}]}], 'generationConfig': gen}
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers=dict(headers, **{'Content-Type': 'application/json'}))
    for attempt in range(4):
        try:
            d = json.load(urllib.request.urlopen(req, timeout=600))
            break
        except urllib.error.HTTPError as e:
            msg = e.read().decode('utf-8', 'ignore')[:300]
            if e.code == 401 and attempt < 3 and 'Authorization' in headers and not cfg.get('token_env'):
                with _TOKEN_LOCK:
                    _TOKENS.pop(cfg.get('account', ''), None)
                url, headers = request(cfg)
                req = urllib.request.Request(url, data=json.dumps(body).encode(), headers=dict(headers, **{'Content-Type': 'application/json'}))
                continue
            if e.code in (429, 500, 503) and attempt < 3:
                time.sleep(5 * (attempt + 1))
                continue
            raise RuntimeError('HTTP %d from %s: %s' % (e.code, url.split('?')[0], msg))
    c = d['candidates'][0]
    reply = ''.join(p.get('text', '') for p in c.get('content', {}).get('parts', []) if not p.get('thought'))
    p = cache_path(cache_key(cfg), prompt)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    json.dump({'model': cfg['model'], 'endpoint': cfg['type'], 'finish': c.get('finishReason'), 'usage': d.get('usageMetadata'),
               'prompt_chars': len(prompt), 'reply': reply, 't': time.strftime('%F %T')}, open(p, 'w'))
    return {'reply': reply, 'usage': d.get('usageMetadata') or {}, 'finish': c.get('finishReason'), 'cached': False}
