import inspect
from pathlib import Path
from typing import List, Optional

import typer
from commonroad.planning.planning_problem import PlanningProblemSet
from commonroad.scenario.scenario import Scenario, Tag
from typing_extensions import Annotated

from crdesigner.common.config.general_config import general_config
from crdesigner.common.config.lanelet2_config import lanelet2_config
from crdesigner.common.file_reader import CRDesignerFileReader
from crdesigner.common.file_writer import CRDesignerFileWriter, OverwriteExistingFile
from crdesigner.map_conversion.map_conversion_interface import (
    commonroad_to_lanelet,
    commonroad_to_sumo,
    lanelet_to_commonroad,
    opendrive_to_commonroad,
    opendrive_to_lanelet,
    osm_to_commonroad,
    sumo_to_commonroad,
)
from crdesigner.ui.gui.start_gui import start_gui
from crdesigner.verification_repairing.config import MapVerParams
from crdesigner.verification_repairing.map_verification_repairing import (
    verify_and_repair_dir_maps,
    verify_and_repair_scenario,
)

cli = typer.Typer(help="Toolbox for Map Conversion and Scenario Creation for Autonomous Vehicles")


def store_scenario(
    sc: Scenario,
    output_file: str,
    force_overwrite: bool,
    author: str,
    affiliation: str,
    tags: Optional[List[str]],
):
    """
    Stores CommonRoad scenario converted via CLI.

    @param sc: CommonRoad scenario.
    @param output_file: Path with file name, where CommonRoad scenario should be stored.
    @param force_overwrite: Boolean indicating whether an existing file should be overwritten.
    @param author: Author of CommonRoad scenario.
    @param affiliation: Affiliation of author of CommonRoad scenario.
    @param tags: Tags of CommonRoad scenario.
    """
    tags = set([Tag(t) for t in tags]) if tags is not None else None
    writer = CRDesignerFileWriter(
        scenario=sc,
        planning_problem_set=PlanningProblemSet(),
        author=author,
        affiliation=affiliation,
        source="CommonRoad Scenario Designer",
        tags=tags,
    )
    if force_overwrite:
        writer.write_to_file(output_file, OverwriteExistingFile.ALWAYS)
    else:
        writer.write_to_file(output_file, OverwriteExistingFile.SKIP)


@cli.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    input_file: Annotated[Optional[Path], typer.Option(help="Path to OpenDRIVE map")] = None,
    output_file: Annotated[
        Optional[Path], typer.Option(help="Path where CommonRoad map should be stored")
    ] = None,
    force_overwrite: Annotated[
        bool, typer.Option(help="Overwrite existing CommonRoad file")
    ] = False,
    author: Annotated[str, typer.Option(..., help="Your name")] = "",
    affiliation: Annotated[
        str,
        typer.Option(..., help="Your affiliation, e.g., university, research institute, company"),
    ] = "",
    tags: Annotated[Optional[List[str]], typer.Option(help="Tags for the created map")] = None,
):
    if ctx.invoked_subcommand is None and input_file is not None:
        start_gui(input_file.name)
    elif ctx.invoked_subcommand is None and input_file is None:
        start_gui()
    else:
        # copied from commonroad-dataset-converter
        frame = inspect.currentframe()
        assert frame is not None
        f_back = frame.f_back
        assert f_back is not None
        kwargs = inspect.getargvalues(f_back)[3]["kwargs"]
        values = locals()
        params = {k: values[k] for k in kwargs.keys() if k not in ["ctx"]}
        ctx.obj = params


@cli.command()
def gui(ctx: typer.Context):
    start_gui(ctx.obj["input_file"])


@cli.command()
def verify_map(ctx: typer.Context):
    sc, pp = CRDesignerFileReader(ctx.obj["input_file"]).open()
    sc, valid = verify_and_repair_scenario(sc)
    if not valid:
        writer = CRDesignerFileWriter(scenario=sc, planning_problem_set=pp)

        file_path = (
            str(ctx.obj["output_file"])
            if ctx.obj["output_file"] is not None
            else str(ctx.obj["input_file"])
        )

        if not ctx.obj["force_overwrite"]:
            file_path = (
                file_path.replace(".xml", "") + "-repaired.xml"
                if file_path[-4:] == ".xml"
                else file_path.replace(".pb", "") + "-repaired.pb"
            )
        writer.write_to_file(file_path)


@cli.command()
def verify_dir(ctx: typer.Context):
    config = MapVerParams()
    config.evaluation.overwrite_scenario = ctx.obj["force_overwrite"]
    verify_and_repair_dir_maps(ctx.obj["input_file"], config)


@cli.command()
def odrcr(ctx: typer.Context):
    scenario = opendrive_to_commonroad(ctx.obj["input_file"])
    store_scenario(
        scenario,
        ctx.obj["output_file"],
        ctx.obj["force_overwrite"],
        ctx.obj["author"],
        ctx.obj["affiliation"],
        ctx.obj["tags"],
    )


@cli.command()
def lanelet2cr(
    ctx: typer.Context,
    proj: Annotated[
        Optional[str], typer.Option(..., help="Overwrite existing CommonRoad file")
    ] = None,
    adjacencies: Annotated[
        bool,
        typer.Option(
            ...,
            help="Detect left and right adjacencies of "
            "lanelets if they do not share a common way",
        ),
    ] = True,
    left_driving: Annotated[
        bool,
        typer.Option(
            ...,
            help="set to true if map describes a left driving " "system, e.g., in Great Britain",
        ),
    ] = False,
):
    config_lanelet2 = lanelet2_config
    if proj is not None:
        general_config.proj_string_cr = proj
    config_lanelet2.adjacencies = adjacencies
    config_lanelet2.left_driving = left_driving
    scenario = lanelet_to_commonroad(ctx.obj["input_file"], lanelet2_conf=config_lanelet2)
    store_scenario(
        scenario,
        ctx.obj["output_file"],
        ctx.obj["force_overwrite"],
        ctx.obj["author"],
        ctx.obj["affiliation"],
        ctx.obj["tags"],
    )


@cli.command()
def crlanelet2(
    ctx: typer.Context,
    proj: Annotated[
        Optional[str], typer.Option(..., help="Overwrite existing CommonRoad file")
    ] = None,
    autoware: Annotated[bool, typer.Option(..., help="Overwrite existing CommonRoad file")] = False,
    local_coordinates: Annotated[
        bool, typer.Option(..., help="Overwrite existing CommonRoad file")
    ] = False,
):
    config = lanelet2_config
    if proj is not None:
        general_config.proj_string_cr = proj
    config.autoware = autoware
    config.use_local_coordinates = local_coordinates
    commonroad_to_lanelet(ctx.obj["input_file"], ctx.obj["output_file"], config=config)


@cli.command()
def osmcr(ctx: typer.Context):
    scenario = osm_to_commonroad(ctx.obj["input_file"])
    store_scenario(
        scenario,
        ctx.obj["output_file"],
        ctx.obj["force_overwrite"],
        ctx.obj["author"],
        ctx.obj["affiliation"],
        ctx.obj["tags"],
    )


@cli.command()
def sumocr(ctx: typer.Context):
    scenario = sumo_to_commonroad(ctx.obj["input_file"])
    store_scenario(
        scenario,
        ctx.obj["output_file"],
        ctx.obj["force_overwrite"],
        ctx.obj["author"],
        ctx.obj["affiliation"],
        ctx.obj["tags"],
    )


@cli.command()
def crsumo(ctx: typer.Context):
    commonroad_to_sumo(ctx.obj["input_file"], ctx.obj["output_file"])


@cli.command()
def odrlanelet2(ctx: typer.Context):
    opendrive_to_lanelet(ctx.obj["input_file"], ctx.obj["output_file"])


if __name__ == "__main__":
    cli()
