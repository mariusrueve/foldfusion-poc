import logging
import subprocess
from pathlib import Path

# Get a logger for this utility module
logger = logging.getLogger(__name__)


def run_command(command, step_name, cwd=None):
    """
    Helper function to run a shell command and handle errors.

    Args:
        command (list): The command and its arguments as a list of strings or Path
                        objects.
        step_name (str): A descriptive name for the step being executed.
        cwd (Path, optional): The working directory to run the command in.
                              Defaults to None (current directory).

    Returns:
        subprocess.CompletedProcess: The result object from subprocess.run.

    Raises:
        subprocess.CalledProcessError: If the command returns a non-zero exit code.
        FileNotFoundError: If the executable is not found.
        Exception: For other unexpected errors.
    """
    logger.info(f"Running {step_name}...")
    # Convert all command parts to strings for subprocess and logging
    cmd_str_list = [str(item) for item in command]
    logger.debug(f"Executing command: {' '.join(cmd_str_list)}")
    effective_cwd = cwd or Path.cwd()
    logger.debug(f"Working directory: {effective_cwd}")
    try:
        result = subprocess.run(
            cmd_str_list,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            cwd=effective_cwd,  # Set working directory
        )
        logger.info(f"{step_name} completed successfully.")
        # Log stdout/stderr only if they contain content and strip whitespace
        stdout_content = result.stdout.strip() if result.stdout else ""
        stderr_content = result.stderr.strip() if result.stderr else ""
        if stdout_content:
            logger.debug(f"{step_name} stdout:\n{stdout_content}")
        if stderr_content:
            # Log stderr as debug unless an error occurs (handled by CalledProcessError)
            logger.debug(f"{step_name} stderr:\n{stderr_content}")
        return result
    except subprocess.CalledProcessError as e:
        logger.error(f"{step_name} failed with exit code {e.returncode}.")
        logger.error(
            f"Command: {' '.join(map(str, e.cmd))}"
        )  # Use original command list with Path objects converted
        # Log stdout/stderr from the exception, stripping whitespace
        stdout_err = e.stdout.strip() if e.stdout else ""
        stderr_err = e.stderr.strip() if e.stderr else ""
        if stdout_err:
            logger.error(f"Stdout:\n{stdout_err}")
        if stderr_err:
            logger.error(f"Stderr:\n{stderr_err}")
        raise  # Re-raise the exception to stop the pipeline
    except FileNotFoundError:
        # Error specific to the executable not being found
        logger.error(f"Error: Executable not found for {step_name} at '{command[0]}'")
        logger.error(
            "Please ensure the path to the executable is correct and it has execute "
            + "permissions."
        )
        raise  # Re-raise
    except Exception as e:
        # Catch-all for other unexpected errors during subprocess execution
        logger.error(f"An unexpected error occurred during {step_name}: {e}")
        raise  # Re-raise


def get_ligands_from_siena_pdb(siena_pdb_path) -> list:
    """
    Extracts ligand information from a SIENA PDB file.

    Args:
        siena_pdb_path (Path): Path to the SIENA PDB file.

    Returns:
        list: A list of tuples containing ligand information.
              Each tuple contains (ligand_name, chain_id, residue_number).
    """
    ligands = []
    with open(siena_pdb_path, "r") as f:
        for line in f:
            if line.startswith("HET "):
                parts = line.split()
                ligand_name = parts[1]
                chain_id = parts[2]
                residue_number = parts[3]
                # Check if the chain ID contains any numbers
                has_number_in_chain = any(char.isdigit() for char in chain_id)
                if has_number_in_chain:
                    logger.warning(
                        f"Found number in chain ID '{chain_id}' for ligand "
                        + f"{ligand_name} at position {residue_number}"
                    )
                    # Split the chain ID after the first character
                    first_char = chain_id[0]
                    remaining_nums = chain_id[1:]
                    # Update residue number to include the numbers from chain ID
                    # Original line: residue_number = remaining_nums + residue_number
                    # Corrected line: Assign remaining_nums as the residue number
                    residue_number = remaining_nums
                    # Update chain ID to just the first character
                    chain_id = first_char
                    logger.info(
                        f"Split chain ID into '{chain_id}' and updated residue "
                        + f"number to {residue_number}"
                    )
                ligands.append(f"{ligand_name}_{chain_id}_{residue_number}")
    return ligands


# if __name__ == "__main__":
#     siena_pdb = Path("pipeline_output/siena/Q9Y233_siena_results/ensemble/3QPN_19.pdb")
#     ligands = get_ligands_from_siena_pdb(siena_pdb)
#     print("Ligands found in SIENA PDB:")
#     for ligand in ligands:
#         print(ligand)
