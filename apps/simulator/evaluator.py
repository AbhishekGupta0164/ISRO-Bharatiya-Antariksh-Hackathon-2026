import heapq
import random
from collections import defaultdict

# ===================== GRAPH =====================


class Graph:
    def __init__(self):
        self.graph = {}

    def add_city(self, city):
        if city not in self.graph:
            self.graph[city] = []

    def add_road(self, city1, city2, distance, pollution):
        self.add_city(city1)
        self.add_city(city2)

        self.graph[city1].append((city2, distance, pollution))
        self.graph[city2].append((city1, distance, pollution))

    def get_neighbors(self, node):
        return self.graph.get(node, [])


# ===================== ROUTING =====================


class Routing:
    def __init__(self, graph: Graph):
        self.graph = graph

    def dijkstra(self, start, end, mode="hybrid", alpha=0.5):
        pq = [(0, start, [], 0, 0, 0)]
        visited = set()

        while pq:
            cost, node, path, dist_sum, poll_sum, exp_sum = heapq.heappop(pq)

            if node in visited:
                continue

            path = path + [node]
            visited.add(node)

            if node == end:
                return {
                    "path": path,
                    "total_distance": dist_sum,
                    "total_pollution": poll_sum,
                    "total_exposure": exp_sum,
                }

            for neighbor, distance, pollution in self.graph.get_neighbors(node):
                if neighbor not in visited:
                    exposure = distance * pollution

                    new_cost = cost + (alpha * distance + (1 - alpha) * exposure)

                    heapq.heappush(
                        pq,
                        (
                            new_cost,
                            neighbor,
                            path,
                            dist_sum + distance,
                            poll_sum + pollution,
                            exp_sum + exposure,
                        ),
                    )
        return None


def get_route(graph, start, end, **kwargs):
    return Routing(graph).dijkstra(start, end, **kwargs)


# ===================== RL ENV =====================


class RLEnv:
    def __init__(self, graph, start, destination):
        self.graph = graph
        self.start = start
        self.destination = destination
        self.max_steps = 20

    def reset(self):
        self.current = self.start
        self.steps = 0
        return self.current

    def get_possible_actions(self):
        return [n[0] for n in self.graph.get_neighbors(self.current)]

    def step(self, action):
        for n, dist, pol in self.graph.get_neighbors(self.current):
            if n == action:
                self.current = n
                self.steps += 1

                reward = -(pol * 0.7 + dist * 0.3)
                reward += 0.5 * max(0, 10 - pol)

                done = n == self.destination

                if done:
                    reward += 100

                if self.steps >= self.max_steps:
                    reward -= 50
                    done = True

                return self.current, reward, done

        raise ValueError("Invalid action")


# ===================== Q-LEARNING =====================


class QAgent:
    def __init__(self):
        self.q = defaultdict(lambda: defaultdict(float))
        self.alpha = 0.1
        self.gamma = 0.9
        self.epsilon = 0.2

    def choose_action(self, state, actions):
        if random.random() < self.epsilon:
            return random.choice(actions)
        return max(actions, key=lambda a: self.q[state][a])

    def update(self, s, a, r, ns, next_actions):
        max_q = max([self.q[ns][na] for na in next_actions], default=0)
        self.q[s][a] += self.alpha * (r + self.gamma * max_q - self.q[s][a])


# ===================== TRAIN =====================


def train_agent(env, agent, episodes=300):
    for _ in range(episodes):
        state = env.reset()
        done = False

        while not done:
            actions = env.get_possible_actions()
            action = agent.choose_action(state, actions)

            next_state, reward, done = env.step(action)

            next_actions = env.get_possible_actions()
            agent.update(state, action, reward, next_state, next_actions)

            state = next_state


# ===================== RL ROUTE =====================


def generate_route(env, agent):
    state = env.reset()
    path = [state]

    done = False

    while not done:
        actions = env.get_possible_actions()
        action = max(actions, key=lambda a: agent.q[state][a])

        next_state, _, done = env.step(action)
        path.append(next_state)
        state = next_state

    return path


# ===================== EXPOSURE CALC =====================


def compute_exposure(graph, path):
    total = 0
    for i in range(len(path) - 1):
        for n, dist, pol in graph.get_neighbors(path[i]):
            if n == path[i + 1]:
                total += dist * pol
    return total


# ===================== MAIN =====================


def run():
    g = Graph()

    g.add_road("A", "B", 5, 10)
    g.add_road("A", "C", 8, 3)
    g.add_road("B", "D", 2, 2)
    g.add_road("C", "D", 4, 6)
    g.add_road("C", "E", 7, 1)
    g.add_road("D", "E", 1, 2)
    g.add_road("D", "F", 6, 8)
    g.add_road("E", "F", 3, 1)

    # Baseline
    baseline = get_route(g, "A", "F")

    # RL
    env = RLEnv(g, "A", "F")
    agent = QAgent()
    train_agent(env, agent)

    rl_path = generate_route(env, agent)

    # Compare
    rl_exposure = compute_exposure(g, rl_path)

    print("\n🚀 RESULTS")
    print("Baseline Path:", " → ".join(baseline["path"]))
    print("Baseline Exposure:", baseline["total_exposure"])

    print("\nRL Path:", " → ".join(rl_path))
    print("RL Exposure:", rl_exposure)


# ===================== RUN =====================

if __name__ == "__main__":
    run()
