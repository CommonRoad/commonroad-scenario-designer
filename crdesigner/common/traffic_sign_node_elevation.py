from commonroad.common.writer.file_writer_xml import TrafficSignXMLNode as OrigNode, Point as OrigPoint

def replace_create_node_with_z():
    """
    Monkey-patch OrigNode.create_node，往 position/point 下追加 <z> 节点。
    """
    original_create = OrigNode.create_node

    def create_node_with_z(traffic_sign):
        # 调用原方法，拿到已经包含 id、elements、2D position、virtual 的节点
        node = original_create(traffic_sign)

        # 拿到 traffic_sign.position 的 z
        pos = traffic_sign.position
        if pos is not None and len(pos) == 3:
            x, y, z = pos

            # 找到 position/point 节点
            pos_node = node.find("position")
            point_node = pos_node.find("point")

            # 用三维数据重建一个 point 节点
            new_point = OrigPoint(x, y, z).create_node()

            # 替换
            pos_node.remove(point_node)
            pos_node.append(new_point)

        return node

    # 真正地替换类方法
    OrigNode.create_node = staticmethod(create_node_with_z)