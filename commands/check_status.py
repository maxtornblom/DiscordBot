import discord
from discord import app_commands
import docker
import os

def setup(client):
    @client.tree.command(name="check_status", description="Check the status of the Minecraft server.")
    async def check_status(interaction: discord.Interaction):
        # Acknowledge the interaction to prevent timeout
        await interaction.response.defer()  

        # Name of your Minecraft Docker container
        container_name = "mcserver1.21.1"

        # Initialize Docker client with the socket path
        # You might need to adjust this path depending on your Docker setup
        docker_client = docker.DockerClient(base_url='unix://var/run/docker.sock')

        # Set up embed template
        embed = discord.Embed(title="Minecraft Server Status", color=discord.Color.green())
        embed.set_thumbnail(url="https://example.com/minecraft_thumbnail.png")  

        try:
            # Fetch container by name
            container = docker_client.containers.get(container_name)
            status = container.status

            # Display server status in embed
            if status == "running":
                embed.add_field(name="Status", value="✅ Server is running!", inline=False)
            elif status == "exited":
                embed.add_field(name="Status", value="❌ Server is not running.", inline=False)
            else:
                embed.add_field(name="Status", value=f"⚠️ Server is in status: `{status.capitalize()}`", inline=False)

            await interaction.followup.send(embed=embed)

        except docker.errors.NotFound:
            # Handle case where container is not found
            embed.add_field(name="Error", value="Container not found. Please check the container name.", inline=False)
            await interaction.followup.send(embed=embed)
        
        except docker.errors.APIError as e:
            # Handle Docker API connection errors
            embed.add_field(name="Error", value=f"Failed to connect to Docker: `{str(e)}`", inline=False)
            await interaction.followup.send(embed=embed)

        except Exception as e:
            # Handle any other exceptions
            embed.add_field(name="Error", value=f"An unexpected error occurred: `{str(e)}`", inline=False)
            await interaction.followup.send(embed=embed)
