from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import random
import threading
import time
import uuid
import webbrowser
from urllib.parse import parse_qs, urlparse

HOST = "127.0.0.1"
PORT = 8765
MAX_SESSIONS = 3
MAX_VARIABLES = 50
MAX_TSP_CITIES = 11
NODE_CAP = 100_000
P_NP_SCENARIOS = {
    "P_equals_NP": {
        "status": "hypothesis_not_testable_by_this_benchmark",
        "meaning": "Would imply polynomial-time algorithms for all NP problems; not demonstrated here.",
    },
    "P_differs_NP": {
        "status": "hypothesis_not_testable_by_this_benchmark",
        "meaning": "Would mean some NP problems lack polynomial-time algorithms; not demonstrated here.",
    },
    "observation": "Finite SAT/TSP timings are compatible with both hypotheses; no result here proves either.",
}
WALKSAT_FLIPS = 20_000

PAGE = """<!doctype html>
<html lang=\"pt-BR\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\"><title>Saturn | Benchmark Console</title>
<style>
:root{color-scheme:dark;--bg:#080d16;--panel:#101927;--line:#233248;--muted:#8da0b8;--text:#e6edf7;--mint:#72f0c0;--blue:#82aaff;--amber:#ffc978;--red:#ff7385}*{box-sizing:border-box}body{margin:0;background:radial-gradient(ellipse at 12% 0%,#15243b 0,transparent 35%),var(--bg);color:var(--text);font:14px/1.5 Inter,ui-sans-serif,system-ui,Segoe UI,sans-serif;min-height:100vh}.shell{max-width:1440px;margin:auto;padding:26px 34px 52px}.top{display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid var(--line);padding-bottom:18px}.brand{display:flex;gap:13px;align-items:center}.mark{width:38px;height:38px;border:1px solid #426d75;border-radius:12px;display:grid;place-items:center;color:var(--mint);font-weight:800;font-size:19px;background:#102a31}.eyebrow,.label,.mono{font-family:ui-monospace,SFMono-Regular,Consolas,monospace;letter-spacing:.12em;text-transform:uppercase;font-size:10px;color:var(--muted)}h1{font-size:20px;margin:0;letter-spacing:-.03em}.sub{color:var(--muted);font-size:12px;margin-top:2px}.pill{border:1px solid var(--line);border-radius:999px;padding:7px 11px;color:var(--muted);font:11px ui-monospace,monospace}.dot{display:inline-block;width:7px;height:7px;border-radius:100%;background:var(--amber);margin-right:8px}.dot.live{background:var(--mint);box-shadow:0 0 12px #72f0c088}.hero{display:flex;justify-content:space-between;align-items:end;gap:20px;padding:31px 0 22px}.hero h2{font-size:30px;line-height:1.1;letter-spacing:-.045em;margin:7px 0}.hero p{color:var(--muted);margin:8px 0 0}.controls{display:flex;gap:8px;align-items:center;flex-wrap:wrap}.controls label{color:var(--muted);font:10px ui-monospace,monospace}.controls input{display:block;background:#0c1420;border:1px solid var(--line);color:var(--text);border-radius:8px;padding:9px;width:94px;margin-top:5px}.btn{border:1px solid #355a58;background:#173a38;color:var(--mint);padding:10px 15px;border-radius:8px;font-weight:700;cursor:pointer}.btn:hover{filter:brightness(1.2)}.btn.stop{border-color:#633a48;background:#341c27;color:#ff9cab}.btn:disabled{opacity:.4;cursor:not-allowed}.grid{display:grid;grid-template-columns:repeat(12,minmax(0,1fr));gap:13px}.card{background:linear-gradient(145deg,#121d2b,#0e1723);border:1px solid var(--line);border-radius:12px;padding:17px;min-width:0}.metric{grid-column:span 3;min-height:105px}.metric .value{font-size:27px;font-weight:700;letter-spacing:-.04em;margin-top:9px}.unit{font-size:11px;color:var(--muted);font-weight:500}.focus{grid-column:span 8;min-height:300px}.aside{grid-column:span 4;min-height:300px}.wide{grid-column:span 7}.tablecard{grid-column:span 5}.cardhead{display:flex;justify-content:space-between;align-items:center;margin-bottom:13px}.cardhead h3{font-size:13px;margin:0;font-weight:650}.tiny{font:10px ui-monospace,monospace;color:var(--muted)}.focusrow{display:flex;justify-content:space-between;gap:16px;align-items:start}.focusname{font-size:19px;font-weight:700}.tag{display:inline-flex;border:1px solid #304155;color:#bdd0e5;border-radius:5px;padding:3px 7px;font:10px ui-monospace,monospace;margin-right:6px}.state{color:var(--mint);font:11px ui-monospace,monospace}.bars{height:164px;display:flex;align-items:end;gap:7px;border-bottom:1px solid var(--line);padding:12px 4px 0;margin-top:18px}.bar{flex:1;min-width:7px;background:linear-gradient(0deg,#316e75,#72f0c0);border-radius:4px 4px 0 0;opacity:.82;position:relative}.bar:nth-child(3n){background:linear-gradient(0deg,#4e5ea1,#82aaff)}.bar:hover{opacity:1}.bar span{position:absolute;top:100%;left:50%;transform:translateX(-50%);font:9px ui-monospace,monospace;color:var(--muted);padding-top:6px}.chartlegend{display:flex;justify-content:space-between;color:var(--muted);font:10px ui-monospace,monospace;margin-top:14px}.branchviz{height:187px;position:relative;overflow:hidden}.branchviz svg{width:100%;height:100%}.branchviz line{stroke:#304760;stroke-width:1.4}.branchviz circle{fill:#142c35;stroke:#72f0c0;stroke-width:1.5}.branchviz circle.pruned{stroke:var(--amber);fill:#382b18}.branchviz text{fill:#a9bed4;font:10px ui-monospace,monospace}.readout{display:grid;gap:13px}.readoutrow{display:flex;justify-content:space-between;gap:10px;border-bottom:1px solid #1d2a3b;padding-bottom:9px}.readoutrow span:first-child{color:var(--muted)}.readoutrow strong{font:12px ui-monospace,monospace;text-align:right}.notice{border-left:2px solid var(--amber);padding:10px 12px;background:#201d19;color:#d5c6aa;font-size:11px;margin-top:13px}.scroll{max-height:245px;overflow:auto}table{width:100%;border-collapse:collapse;text-align:left;font-size:11px}th{font:9px ui-monospace,monospace;color:var(--muted);text-transform:uppercase;letter-spacing:.08em;padding:8px 5px;border-bottom:1px solid var(--line)}td{padding:9px 5px;border-bottom:1px solid #1c2838;color:#c5d1df}td:last-child{font-family:ui-monospace,monospace;color:var(--mint)}.empty{color:var(--muted);padding:22px 4px;text-align:center}.foot{color:#71839a;font-size:10px;margin-top:16px}.error{color:var(--red)}@media(max-width:900px){.metric{grid-column:span 6}.focus,.aside,.wide,.tablecard{grid-column:span 12}.hero{align-items:start;flex-direction:column}.shell{padding:20px 16px 40px}}@media(max-width:500px){.top{align-items:start}.pill{font-size:9px}.hero h2{font-size:25px}.metric{grid-column:span 6;padding:13px}.metric .value{font-size:22px}.controls{width:100%}.controls label{flex:1}.btn{flex:1}}
</style></head><body><main class=\"shell\">
<header class=\"top\"><div class=\"brand\"><div class=\"mark\">Σ</div><div><h1>Saturn <span style=\"color:var(--muted);font-weight:400\">/ benchmark console</span></h1><div class=\"sub\">SAT · branch-and-bound TSP · local runtime</div></div></div><div class=\"pill\"><i id=\"dot\" class=\"dot\"></i><span id=\"connection\">AGUARDANDO PROCESSO</span></div></header>
<section class=\"hero\"><div><div class=\"eyebrow\">Computational experiment / 01</div><h2>Exploração de instâncias</h2><p>Busca incremental, filtragem de ramos e atualização em ciclos contínuos.</p></div><div class=\"controls\"><label>VARS INICIAIS<input id=\"start\" type=\"number\" value=\"8\" min=\"3\" max=\"50\"></label><label>CLAUSES / VAR<input id=\"ratio\" type=\"number\" value=\"4.2\" min=\"1\" max=\"10\" step=\"0.1\"></label><button id=\"startBtn\" class=\"btn\">▶ Iniciar benchmark</button><button id=\"stopBtn\" class=\"btn stop\" disabled>■ Desligar</button></div></section>
<section class=\"grid\"><article class=\"card metric\"><div class=\"label\">Casos concluídos</div><div class=\"value\" id=\"cases\">—</div></article><article class=\"card metric\"><div class=\"label\">Ciclos completos</div><div class=\"value\" id=\"cycles\">—</div></article><article class=\"card metric\"><div class=\"label\">Problema atual</div><div class=\"value\" id=\"problem\">—</div></article><article class=\"card metric\"><div class=\"label\">Ramos filtrados</div><div class=\"value\" id=\"pruned\">—</div></article>
<article class=\"card focus\"><div class=\"cardhead\"><h3>Atividade recente</h3><span class=\"tiny\" id=\"seed\">SEED —</span></div><div id=\"activity\"><div class=\"empty\">Inicie o benchmark para observar o fluxo de avaliação.</div></div><div class=\"chartlegend\"><span>HISTÓRICO DE CASOS PROCESSADOS</span><span id=\"chartcount\">0 / 12</span></div></article>
<article class=\"card aside\"><div class=\"cardhead\"><h3>Árvore de decisão</h3><span class=\"tiny\">PILHA / PODA</span></div><div class=\"branchviz\"><svg viewBox=\"0 0 360 190\" aria-label=\"Ilustração da expansão da busca\"><line x1=\"180\" y1=\"23\" x2=\"103\" y2=\"77\"/><line x1=\"180\" y1=\"23\" x2=\"257\" y2=\"77\"/><line x1=\"103\" y1=\"77\" x2=\"57\" y2=\"132\"/><line x1=\"103\" y1=\"77\" x2=\"148\" y2=\"132\"/><line x1=\"257\" y1=\"77\" x2=\"212\" y2=\"132\"/><line x1=\"257\" y1=\"77\" x2=\"303\" y2=\"132\"/><circle cx=\"180\" cy=\"23\" r=\"9\"/><circle cx=\"103\" cy=\"77\" r=\"8\"/><circle cx=\"257\" cy=\"77\" r=\"8\"/><circle cx=\"57\" cy=\"132\" r=\"7\"/><circle cx=\"148\" cy=\"132\" r=\"7\"/><circle class=\"pruned\" cx=\"212\" cy=\"132\" r=\"7\"/><circle cx=\"303\" cy=\"132\" r=\"7\"/><text x=\"191\" y=\"27\">raiz</text><text x=\"43\" y=\"158\">viável</text><text x=\"195\" y=\"158\">poda</text></svg></div><div class=\"readout\"><div class=\"readoutrow\"><span>Estado da busca exata</span><strong id=\"exact\">—</strong></div><div class=\"readoutrow\"><span>Heurística / incumbente</span><strong id=\"heuristic\">—</strong></div><div class=\"readoutrow\"><span>Trabalho acumulado</span><strong id=\"work\">—</strong></div></div></article>
<article class=\"card wide\"><div class=\"cardhead\"><h3>Histórico de avaliação</h3><span class=\"tiny\">ÚLTIMOS CASOS</span></div><div class=\"scroll\"><table><thead><tr><th>Tipo / família</th><th>Escala</th><th>Busca exata</th><th>Resultado</th></tr></thead><tbody id=\"history\"><tr><td colspan=\"4\" class=\"empty\">Nenhum caso registrado.</td></tr></tbody></table></div></article>
<article class=\"card tablecard\"><div class=\"cardhead\"><h3>Hipóteses P vs NP</h3><span class=\"tiny\">STATUS CIENTÍFICO</span></div><div class=\"readout\"><div class=\"readoutrow\"><span>P = NP</span><strong>NÃO DETERMINADO</strong></div><div class=\"readoutrow\"><span>P ≠ NP</span><strong>NÃO DETERMINADO</strong></div></div><div class=\"notice\">Benchmarks finitos medem instâncias específicas. Não provam nem refutam hipóteses sobre algoritmos polinomiais para todos os casos.</div><div class=\"foot\">Local loopback · 127.0.0.1 · limite por instância ativo</div></article></section>
</main><script>
let sid=null,poller=null;const $=id=>document.getElementById(id),startBtn=$('startBtn'),stopBtn=$('stopBtn');let history=[];
function setConnection(on,text){$('dot').classList.toggle('live',on);$('connection').textContent=text}
function render(s){$('cases').textContent=s.completed_cases.toLocaleString('pt-BR');$('cycles').textContent=s.completed_cycles.toLocaleString('pt-BR');const c=s.current;$('problem').textContent=c?c.type:'—';$('pruned').textContent=c&&c.branches_pruned!=null?c.branches_pruned.toLocaleString('pt-BR'):'—';$('exact').textContent=c?c.exact:'—';$('heuristic').textContent=c?(c.heuristic||('custo '+c.heuristic_cost)):'—';$('work').textContent=c?(c.dpll_nodes!=null?c.dpll_nodes.toLocaleString('pt-BR')+' nós · '+c.walksat_flips+' flips':c.nodes.toLocaleString('pt-BR')+' nós · '+c.branches_pruned+' podas'):'—';if(c){$('seed').textContent=(c.family||'CASO')+' · '+(c.variables?c.variables+' vars / '+c.clauses+' cláusulas':c.cities+' cidades');$('activity').innerHTML='<div class=\"focusrow\"><div><span class=\"tag\">'+c.type+'</span><span class=\"tag\">'+(c.family||'benchmark')+'</span><div class=\"focusname\" style=\"margin-top:12px\">'+(c.type==='SAT'?c.variables+' variáveis · '+c.clauses+' cláusulas':c.cities+' cidades · custo atual '+c.best_tour_cost)+'</div><div class=\"sub\" style=\"margin-top:6px\">Busca incremental em execução; a sessão atualiza após cada fatia de trabalho.</div></div><div class=\"state\">● '+(c.completed?'CONCLUÍDO':'PROCESSANDO')+'</div></div><div class=\"bars\">'+history.slice(-24).map((x,i)=>'<div class=\"bar\" style=\"height:'+Math.max(12,Math.min(96,18+(x.dpll_nodes||x.nodes||1)%78))+'%\" title=\"'+x.type+' · '+x.family+'\"><span>'+(i+1)+'</span></div>').join('')+'<div class=\"bar\" style=\"height:82%;opacity:.45\"><span>agora</span></div></div>'}history=s.recent_results||[];$('chartcount').textContent=history.length+' / 12';const rows=history.slice(-12).reverse();$('history').innerHTML=rows.length?rows.map(x=>'<tr><td>'+x.type+' / '+x.family+'</td><td>'+(x.variables?x.variables+' vars':x.cities+' cidades')+'</td><td>'+x.exact+'</td><td>'+(x.candidate_validated?'SAT verificado':x.best_tour_cost!=null?'custo '+x.best_tour_cost:x.heuristic||'—')+'</td></tr>').join(''):'<tr><td colspan=\"4\" class=\"empty\">Nenhum caso registrado.</td></tr>'}
async function poll(){if(!sid)return;try{const r=await fetch('/api/status?id='+encodeURIComponent(sid));const s=await r.json();if(!r.ok)throw Error(s.error||r.status);render(s);setConnection(s.state==='running',s.state==='running'?'BENCHMARK ATIVO':'PROCESSO DESLIGADO');if(s.state==='stopped'){clearInterval(poller);poller=null;sid=null;startBtn.disabled=false;stopBtn.disabled=true}}catch(e){setConnection(false,'CONEXÃO PERDIDA');$('activity').innerHTML='<div class=\"empty error\">'+e+'</div>'}}
async function start(){startBtn.disabled=true;try{const r=await fetch('/api/start',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({start:+$('start').value,ratio:+$('ratio').value})});const s=await r.json();if(!r.ok)throw Error(s.error||r.status);sid=s.id;stopBtn.disabled=false;setConnection(true,'BENCHMARK ATIVO');await poll();poller=setInterval(poll,500)}catch(e){setConnection(false,'FALHA AO INICIAR');$('activity').innerHTML='<div class=\"empty error\">'+e+'</div>';startBtn.disabled=false}}
startBtn.onclick=start;stopBtn.onclick=async()=>{if(!sid)return;stopBtn.disabled=true;await fetch('/api/stop',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id:sid})});await poll()};
if(new URLSearchParams(location.search).get('autostart')==='1')start();
</script></body></html>"""


def random_3sat(nvars, nclauses, rng, planted=False):
    hidden = [False] + [bool(rng.randrange(2)) for _ in range(nvars)] if planted else None
    clauses = []
    for _ in range(nclauses):
        vars_ = rng.sample(range(1, nvars + 1), min(3, nvars))
        lits = [v if rng.randrange(2) else -v for v in vars_]
        if planted and not any(hidden[abs(l)] == (l > 0) for l in lits):
            chosen = rng.randrange(len(lits))
            v = abs(lits[chosen])
            lits[chosen] = v if hidden[v] else -v
        clauses.append(tuple(lits))
    return clauses


def random_mixed_sat(nvars, nclauses, rng):
    clauses = []
    for _ in range(nclauses):
        width = rng.choice((2, 3, 3, 4))
        vars_ = rng.sample(range(1, nvars + 1), min(width, nvars))
        clauses.append(tuple(v if rng.randrange(2) else -v for v in vars_))
    return clauses


def unit_propagate(clauses, assignment):
    clauses = list(clauses)
    while True:
        simplified, units = [], []
        for clause in clauses:
            remaining, satisfied = [], False
            for lit in clause:
                value = assignment.get(abs(lit))
                if value is None:
                    remaining.append(lit)
                elif value == (lit > 0):
                    satisfied = True
                    break
            if not satisfied:
                if not remaining:
                    return None
                if len(remaining) == 1:
                    units.append(remaining[0])
                else:
                    simplified.append(tuple(remaining))
        if not units:
            return simplified
        for lit in units:
            var, val = abs(lit), lit > 0
            if var in assignment and assignment[var] != val:
                return None
            assignment[var] = val
        clauses = simplified


class DPLLSearch:
    """Incremental exact DFS; stack frames retain branches across updates."""
    def __init__(self, clauses, node_cap=NODE_CAP):
        self.clauses = clauses
        self.pending = [{}]
        self.nodes = 0
        self.node_cap = node_cap
        self.state = "running"
        self.solution = None

    def advance(self, slice_nodes=300):
        if self.state != "running":
            return self.state
        end = self.nodes + slice_nodes
        while self.pending and self.nodes < end and self.nodes < self.node_cap:
            assignment = self.pending.pop()
            self.nodes += 1
            reduced = unit_propagate(self.clauses, assignment)
            if reduced is None:
                continue
            if not reduced:
                self.solution, self.state = assignment, "SAT"
                return self.state
            # Minimum-remaining-clause heuristic; both values remain on stack.
            clause = min(reduced, key=len)
            var = max({abs(lit) for lit in clause},
                      key=lambda v: sum(v in {abs(x) for x in c} for c in reduced))
            branch_true, branch_false = dict(assignment), dict(assignment)
            branch_true[var], branch_false[var] = True, False
            self.pending.extend((branch_false, branch_true))
        if not self.pending:
            self.state = "UNSAT"
        elif self.nodes >= self.node_cap:
            self.state = "resource_cap"
        return self.state


def verify_tour(matrix, tour):
    n = len(matrix)
    return (tour is not None and len(tour) == n and len(set(tour)) == n
            and set(tour) == set(range(n)))


def tour_cost(matrix, tour):
    return sum(matrix[tour[i]][tour[(i + 1) % len(tour)]] for i in range(len(tour)))


def nearest_neighbor(matrix):
    n = len(matrix)
    best = None
    for start in range(n):
        tour, remaining, total = [start], set(range(n)) - {start}, 0
        while remaining:
            nxt = min(remaining, key=lambda city: matrix[tour[-1]][city])
            total += matrix[tour[-1]][nxt]
            tour.append(nxt)
            remaining.remove(nxt)
        total += matrix[tour[-1]][start]
        if best is None or total < best[0]:
            best = (total, tour)
    return best


class TSPBranchBound:
    """Exact stack-based TSP with admissible outgoing-edge lower bound."""
    def __init__(self, matrix, node_cap=NODE_CAP):
        self.matrix = matrix
        self.n = len(matrix)
        self.node_cap = node_cap
        initial = nearest_neighbor(matrix)
        self.best_cost, self.best_tour = initial
        self.pending = [((0,), 0)]
        self.nodes = 0
        self.pruned = 0
        self.state = "running"

    def lower_bound(self, path, cost):
        remaining = set(range(self.n)) - set(path)
        endpoint = path[-1]
        if not remaining:
            return cost + self.matrix[endpoint][path[0]]
        bound = cost + min(self.matrix[endpoint][v] for v in remaining)
        # Each unvisited vertex must leave once; allowing any destination
        # (including already visited ones) only makes this bound optimistic.
        for city in remaining:
            bound += min(self.matrix[city][v] for v in range(self.n) if v != city)
        return bound

    def advance(self, slice_nodes=300):
        if self.state != "running":
            return self.state
        end = self.nodes + slice_nodes
        while self.pending and self.nodes < end and self.nodes < self.node_cap:
            path, cost = self.pending.pop()
            self.nodes += 1
            if len(path) == self.n:
                total = cost + self.matrix[path[-1]][path[0]]
                if total < self.best_cost:
                    self.best_cost, self.best_tour = total, path
                continue
            if self.lower_bound(path, cost) >= self.best_cost:
                self.pruned += 1
                continue
            last = path[-1]
            choices = sorted((v for v in range(self.n) if v not in path),
                             key=lambda v: self.matrix[last][v])
            for city in reversed(choices):
                new_cost = cost + self.matrix[last][city]
                if new_cost >= self.best_cost:
                    self.pruned += 1
                    continue
                self.pending.append((path + (city,), new_cost))
        if not self.pending:
            self.state = "optimal"
        elif self.nodes >= self.node_cap:
            self.state = "resource_cap"
        return self.state


def make_matrix(n, rng, symmetric=False):
    matrix = [[0 if i == j else rng.randint(1, 100) for j in range(n)] for i in range(n)]
    if symmetric:
        for i in range(n):
            for j in range(i + 1, n):
                matrix[j][i] = matrix[i][j]
    return matrix


class WalkSATSearch:
    def __init__(self, clauses, nvars, rng, max_flips=WALKSAT_FLIPS):
        self.clauses, self.nvars, self.rng = clauses, nvars, rng
        self.max_flips, self.flips, self.tries = max_flips, 0, 0
        self.values, self.solution, self.state = None, None, "running"
        self._restart()

    def _restart(self):
        self.values = [False] + [bool(self.rng.randrange(2)) for _ in range(self.nvars)]
        self.tries += 1

    def advance(self, slice_flips=100):
        if self.state != "running":
            return self.state
        end = min(self.flips + slice_flips, self.max_flips)
        while self.flips < end:
            unsat = [c for c in self.clauses
                     if not any(self.values[abs(l)] == (l > 0) for l in c)]
            if not unsat:
                self.solution, self.state = self.values[1:].copy(), "SAT_candidate"
                return self.state
            clause = self.rng.choice(unsat)
            if self.rng.random() < 0.35:
                lit = self.rng.choice(clause)
            else:
                lit = max(clause, key=lambda x: sum(
                    any(self.values[abs(y)] == (y > 0) for y in c if abs(y) != abs(x))
                    for c in self.clauses))
            self.values[abs(lit)] = not self.values[abs(lit)]
            self.flips += 1
            if self.flips % 2500 == 0:
                self._restart()
        if self.flips >= self.max_flips:
            self.state = "not_found"
        return self.state


class Session:
    def __init__(self, start, ratio):
        self.id = uuid.uuid4().hex[:12]
        self.start_vars, self.ratio = start, ratio
        self.lock = threading.Lock()
        self.stop_event = threading.Event()
        self.state = "running"
        self.cycle = 0
        self.completed = 0
        self.current = None
        self.history = []
        self.cases = []
        self.case_index = 0
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def _make_cycle(self, cycle):
        cases = []
        base = min(self.start_vars + cycle, MAX_VARIABLES)
        for flavor_index, flavor in enumerate(("random-3sat", "planted-3sat", "mixed-k-sat")):
            nvars = min(MAX_VARIABLES, base + flavor_index)
            nclauses = max(nvars, round(nvars * self.ratio))
            seed = (int(self.id, 16) + cycle * 1_000_003 + flavor_index * 104729) & 0xffffffff
            rng = random.Random(seed)
            if flavor == "mixed-k-sat":
                clauses = random_mixed_sat(nvars, nclauses, rng)
            else:
                clauses = random_3sat(nvars, nclauses, rng, planted=(flavor == "planted-3sat"))
            cases.append({"type": "SAT", "family": flavor, "variables": nvars,
                          "clauses": nclauses, "seed": seed, "formula": clauses,
                          "exact": DPLLSearch(clauses),
                          "heuristic": WalkSATSearch(clauses, nvars, random.Random(seed ^ 0x5A17))})
        tsp_n = min(5 + (cycle % (MAX_TSP_CITIES - 4)), MAX_TSP_CITIES)
        tsp_seed = (int(self.id, 16) + cycle * 2_000_033 + 991) & 0xffffffff
        matrix = make_matrix(tsp_n, random.Random(tsp_seed), symmetric=(cycle % 2 == 0))
        greedy_cost, greedy_tour = nearest_neighbor(matrix)
        cases.append({"type": "TSP", "family": "random-symmetric" if cycle % 2 == 0 else "random-directed",
                      "cities": tsp_n, "seed": tsp_seed, "matrix": matrix,
                      "exact": TSPBranchBound(matrix), "heuristic_cost": greedy_cost,
                      "heuristic_tour": greedy_tour})
        return cases

    def _run(self):
        while not self.stop_event.is_set():
            if not self.cases:
                self.cases = self._make_cycle(self.cycle)
                self.case_index = 0
            item = self.cases[self.case_index]
            exact_state = item["exact"].advance()
            if item["type"] == "SAT":
                heuristic_state = item["heuristic"].advance()
            else:
                heuristic_state = "heuristic_ready"
            with self.lock:
                self.current = self._summary(item, exact_state, heuristic_state)
            if exact_state != "running" and (item["type"] == "TSP" or heuristic_state != "running"):
                record = self._summary(item, exact_state, heuristic_state)
                with self.lock:
                    self.history.append(record)
                    if len(self.history) > 1000:
                        del self.history[:-1000]
                    self.completed += 1
                self.case_index += 1
                if self.case_index >= len(self.cases):
                    self.cycle += 1
                    self.cases = []  # completion loop: generate fresh seeded cases
                else:
                    self.current = None
            else:
                time.sleep(0.003)
        with self.lock:
            self.state = "stopped"

    @staticmethod
    def _summary(item, exact_state, heuristic_state):
        result = {"type": item["type"], "family": item["family"],
                  "exact": exact_state, "completed": exact_state != "running"}
        if item["type"] == "SAT":
            candidate = item["heuristic"].solution
            valid = candidate is not None and all(
                any(candidate[abs(lit) - 1] == (lit > 0) for lit in clause)
                for clause in item["formula"])
            result.update({"variables": item["variables"], "clauses": item["clauses"],
                           "heuristic": heuristic_state, "candidate_validated": valid,
                           "dpll_nodes": item["exact"].nodes,
                           "walksat_flips": item["heuristic"].flips})
        else:
            result.update({"cities": item["cities"], "heuristic_cost": item["heuristic_cost"],
                           "best_tour_cost": item["exact"].best_cost,
                           "tour_valid": verify_tour(item["matrix"], item["exact"].best_tour),
                           "nodes": item["exact"].nodes, "branches_pruned": item["exact"].pruned})
        result["P_vs_NP_scenarios"] = P_NP_SCENARIOS
        return result

    def snapshot(self):
        with self.lock:
            return {"id": self.id, "state": self.state, "completed_cases": self.completed,
                    "completed_cycles": self.cycle, "current": self.current,
                    "recent_results": self.history[-12:],
                    "scientific_status": "Empirical measurements only; neither P=NP nor P!=NP can be inferred.",
                    "limits": {"max_variables": MAX_VARIABLES, "max_tsp_cities": MAX_TSP_CITIES,
                               "nodes_per_exact_search": NODE_CAP,
                               "walksat_flips": WALKSAT_FLIPS}}

    def stop(self):
        self.stop_event.set()


sessions = {}
sessions_lock = threading.Lock()


def start_session(params):
    try:
        start, ratio = int(params.get("start", 8)), float(params.get("ratio", 4.2))
    except (ValueError, TypeError) as exc:
        raise ValueError("Parâmetros numéricos inválidos") from exc
    if not 3 <= start <= MAX_VARIABLES or not 1 <= ratio <= 10:
        raise ValueError("Limites: start 3–50, ratio 1–10")
    with sessions_lock:
        active = sum(s.state == "running" for s in sessions.values())
        if active >= MAX_SESSIONS:
            raise ValueError(f"Limite de {MAX_SESSIONS} sessões simultâneas atingido")
        session = Session(start, ratio)
        sessions[session.id] = session
        return session


class Handler(BaseHTTPRequestHandler):
    def _json(self, status, value):
        body = json.dumps(value, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed_url = urlparse(self.path)
        if parsed_url.path == "/":
            body = PAGE.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
        elif parsed_url.path == "/api/status":
            sid = parse_qs(parsed_url.query).get("id", [""])[0]
            session = sessions.get(sid)
            if not session:
                self._json(404, {"error": "Sessão não encontrada"})
                return
            body = json.dumps(session.snapshot(), ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_error(404)
            return
        if parsed_url.path == "/":
            self.wfile.write(body)

    def do_POST(self):
        try:
            size = int(self.headers.get("Content-Length", "0"))
            params = json.loads(self.rfile.read(size) or b"{}")
            if self.path == "/api/start":
                session = start_session(params)
                self._json(202, session.snapshot())
            elif self.path == "/api/stop":
                session = sessions.get(str(params.get("id", "")))
                if not session:
                    self._json(404, {"error": "Sessão não encontrada"})
                else:
                    session.stop()
                    self._json(202, {"id": session.id, "state": "stopping"})
            else:
                self.send_error(404)
        except (ValueError, TypeError, json.JSONDecodeError) as exc:
            self._json(400, {"error": str(exc)})

    def log_message(self, fmt, *args):
        print("%s - %s" % (self.address_string(), fmt % args))


if __name__ == "__main__":
    url = f"http://{HOST}:{PORT}/?autostart=1"
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"Benchmark e painel local: {url}", flush=True)
    print("Acesso limitado a este computador (127.0.0.1). Feche com Ctrl+C.", flush=True)
    threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Encerrando benchmark/painel...", flush=True)
    finally:
        for session in list(sessions.values()):
            session.stop()
        server.server_close()
