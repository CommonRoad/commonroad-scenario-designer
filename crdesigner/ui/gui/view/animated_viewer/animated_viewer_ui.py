class AnimatedViewerUI:
    def draw_lanelet_vertices(self, lanelet, ax):
        ax.plot(
            [x for x, y in lanelet.left_vertices[:, :2]],
            [y for x, y in lanelet.left_vertices[:, :2]],
            color="black",
            lw=0.1,
        )
        ax.plot(
            [x for x, y in lanelet.right_vertices[:, :2]],
            [y for x, y in lanelet.right_vertices[:, :2]],
            color="black",
            lw=0.1,
        )
