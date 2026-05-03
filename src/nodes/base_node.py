class BaseNode:
    def __init__(self, node_id, peers):
        self.node_id = node_id
        self.peers = peers
        self.state = "follower"
        self.leader_id = None

    def is_leader(self):
        return self.state == "leader"