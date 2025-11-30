"""
LLM Agent with map control tools
The model can query data AND control the map display
"""
import json
import os
from typing import Any
from groq import Groq
from service import MappingService
from models.domain import Campaign


# Tool definitions for the LLM
MAPPING_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "show_features",
            "description": "Find and highlight features on the map. Use this when user says 'show me X' or 'find X'. This will query AND highlight in one step.",
            "parameters": {
                "type": "object",
                "properties": {
                    "feature_type": {
                        "type": "string",
                        "enum": [
                            "pavement_damage", "road_marking", "manhole_cover", "drainage_grate", "pavement_patch",
                            "traffic_sign", "street_light", "utility_pole", "trash_bin", "fire_hydrant", 
                            "traffic_light", "vegetation", "all"
                        ],
                        "description": "Type of feature to show (horizontal: pavement_damage, road_marking, manhole_cover, drainage_grate, pavement_patch; vertical: traffic_sign, street_light, utility_pole, trash_bin, fire_hydrant, traffic_light, vegetation)"
                    },
                    "condition": {
                        "type": "string",
                        "enum": ["good", "fair", "poor", "damaged", "any"],
                        "description": "Condition filter"
                    },
                    "color": {
                        "type": "string",
                        "description": "Hex color for highlights (default: #FF0000)",
                        "default": "#FF0000"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "query_images",
            "description": "Query image positions (camera locations) from the campaign",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "find_images_with_features",
            "description": "Find image positions that contain specific features. Use this for questions like 'which images have traffic signs' or 'images containing damaged features'",
            "parameters": {
                "type": "object",
                "properties": {
                    "feature_type": {
                        "type": "string",
                        "enum": [
                            "pavement_damage", "road_marking", "manhole_cover", "drainage_grate", "pavement_patch",
                            "traffic_sign", "street_light", "utility_pole", "trash_bin", "fire_hydrant", 
                            "traffic_light", "vegetation", "any"
                        ],
                        "description": "Type of feature to look for in images"
                    },
                    "condition": {
                        "type": "string",
                        "enum": ["good", "fair", "poor", "damaged", "any"],
                        "description": "Condition filter for features"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "find_richest_image",
            "description": "Find the image position with the most features. Optionally filter by feature type or condition.",
            "parameters": {
                "type": "object",
                "properties": {
                    "feature_type": {
                        "type": "string",
                        "enum": [
                            "pavement_damage", "road_marking", "manhole_cover", "drainage_grate", "pavement_patch",
                            "traffic_sign", "street_light", "utility_pole", "trash_bin", "fire_hydrant", 
                            "traffic_light", "vegetation", "any"
                        ],
                        "description": "Optional: filter to specific feature type"
                    },
                    "condition": {
                        "type": "string",
                        "enum": ["good", "fair", "poor", "damaged", "any"],
                        "description": "Optional: filter by condition"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "highlight_on_map",
            "description": "Highlight specific features on the map with a color",
            "parameters": {
                "type": "object",
                "properties": {
                    "feature_ids": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "List of feature IDs to highlight"
                    },
                    "color": {
                        "type": "string",
                        "description": "Hex color code (e.g., #FF0000 for red, #00FF00 for green)"
                    },
                    "label": {
                        "type": "string",
                        "description": "Optional label for this highlight group"
                    }
                },
                "required": ["feature_ids"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "show_statistics",
            "description": "Display statistics on the map as an info box",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Title of the statistics box"
                    },
                    "stats": {
                        "type": "object",
                        "description": "Key-value pairs of statistics to display"
                    }
                },
                "required": ["title", "stats"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "clear_map",
            "description": "Clear all highlights and info boxes from the map",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    }
]


class MappingAgent:
    """LLM agent that can query data and control the map"""
    
    def __init__(self, api_key: str):
        self.client = Groq(api_key=api_key)
        self.campaign = MappingService.get_campaign()
        self.conversation_history = []  # Maintain context between questions
    
    def execute_tool(self, tool_name: str, tool_input: dict) -> dict:
        """Execute a tool and return results + map commands"""
        
        if tool_name == "show_features":
            # Combined: query + highlight in one step
            feature_type = tool_input.get("feature_type", "all")
            condition = tool_input.get("condition", "any")
            color = tool_input.get("color", "#FF0000")
            
            filtered = self.campaign.features
            
            if feature_type != "all":
                filtered = [f for f in filtered if f.type == feature_type]
            
            if condition != "any":
                filtered = [f for f in filtered if f.condition == condition]
            
            feature_ids = [f.id for f in filtered]
            
            # Return both data and map command
            return {
                "count": len(filtered),
                "feature_ids": feature_ids,
                "map_command": {
                    "command": "highlight_features",
                    "feature_ids": feature_ids,
                    "color": color,
                    "label": feature_type.replace("_", " ").title()
                },
                "message": f"Found and highlighted {len(filtered)} {feature_type} features"
            }
        
        elif tool_name == "query_images":
            # Query image positions
            image_count = len(self.campaign.images)
            return {
                "count": image_count,
                "message": f"Campaign has {image_count} image positions (shown as blue camera dots on the map)"
            }
        
        elif tool_name == "find_images_with_features":
            # Find images containing specific features
            feature_type = tool_input.get("feature_type", "any")
            condition = tool_input.get("condition", "any")
            
            # Filter features first
            filtered_features = self.campaign.features
            if feature_type != "any":
                filtered_features = [f for f in filtered_features if f.type == feature_type]
            if condition != "any":
                filtered_features = [f for f in filtered_features if f.condition == condition]
            
            feature_ids = set(f.id for f in filtered_features)
            
            # Find images that contain these features
            matching_images = []
            matching_image_ids = []
            for img in self.campaign.images:
                img_features = set(img.feature_ids) & feature_ids
                if img_features:
                    matching_images.append({
                        "image_id": img.id,
                        "feature_count": len(img_features),
                        "coordinates": img.geometry["coordinates"]
                    })
                    matching_image_ids.append(img.id)
            
            # Highlight both features and images
            map_commands = []
            if filtered_features:
                map_commands.append({
                    "command": "highlight_features",
                    "feature_ids": [f.id for f in filtered_features],
                    "color": "#00FF00",
                    "label": f"{feature_type} features"
                })
            if matching_image_ids:
                map_commands.append({
                    "command": "highlight_image",
                    "image_ids": matching_image_ids,
                    "color": "#4A90E2",
                    "label": f"Images with {feature_type}"
                })
            
            return {
                "image_count": len(matching_images),
                "images": matching_images,
                "feature_count": len(filtered_features),
                "map_commands": map_commands,
                "message": f"Found {len(matching_images)} images containing {len(filtered_features)} matching features"
            }
        
        elif tool_name == "find_richest_image":
            # Find image with most features
            feature_type = tool_input.get("feature_type", "any")
            condition = tool_input.get("condition", "any")
            
            # Filter features
            filtered_features = self.campaign.features
            if feature_type != "any":
                filtered_features = [f for f in filtered_features if f.type == feature_type]
            if condition != "any":
                filtered_features = [f for f in filtered_features if f.condition == condition]
            
            feature_ids = set(f.id for f in filtered_features)
            
            # Count features per image
            richest_image = None
            max_count = 0
            
            for img in self.campaign.images:
                img_features = set(img.feature_ids) & feature_ids
                if len(img_features) > max_count:
                    max_count = len(img_features)
                    richest_image = {
                        "image_id": img.id,
                        "feature_count": max_count,
                        "coordinates": img.geometry["coordinates"],
                        "feature_ids": list(img_features)
                    }
            
            # Highlight the features from richest image
            map_command = None
            if richest_image:
                map_command = {
                    "command": "highlight_features",
                    "feature_ids": richest_image["feature_ids"],
                    "color": "#FF00FF",
                    "label": f"Image {richest_image['image_id']}"
                }
            
            return {
                "richest_image": richest_image,
                "map_command": map_command,
                "message": f"Image {richest_image['image_id']} has the most features ({max_count})" if richest_image else "No matching images found"
            }
        
        elif tool_name == "highlight_on_map":
            # Validate feature_ids
            feature_ids = tool_input.get("feature_ids", [])
            if not feature_ids:
                return {
                    "error": "No feature_ids provided. You must first call query_features to get feature IDs, then pass those IDs to highlight_on_map."
                }
            
            # Return a map command
            return {
                "map_command": {
                    "command": "highlight_features",
                    "feature_ids": feature_ids,
                    "color": tool_input.get("color", "#FF0000"),
                    "label": tool_input.get("label")
                },
                "message": f"Highlighted {len(feature_ids)} features on the map"
            }
        
        elif tool_name == "show_statistics":
            # Return a map command
            return {
                "map_command": {
                    "command": "show_statistics",
                    "title": tool_input["title"],
                    "stats": tool_input["stats"]
                },
                "message": f"Displayed statistics: {tool_input['title']}"
            }
        
        elif tool_name == "clear_map":
            return {
                "map_command": {
                    "command": "clear_highlights"
                },
                "message": "Cleared all highlights from the map"
            }
        
        return {"error": f"Unknown tool: {tool_name}"}
    
    def ask(self, question: str) -> dict:
        """
        Process a natural language question and return:
        - Answer text
        - Tool uses
        - Map commands to execute
        """
        
        # System prompt to guide the model
        system_prompt = f"""You are a helpful assistant for a mobile mapping campaign in San Bernardino with {self.campaign.total_features} features and {self.campaign.total_images} image positions.

Use the provided tools to answer user questions. Your text responses should be plain, natural language only.

TOOL USAGE:
- show_features: Show/find features on map
- find_images_with_features: Find which images contain specific features
- find_richest_image: Find image position with most features
- query_images: Get total image count

HORIZONTAL FEATURES (on ground): pavement_damage, road_marking, manhole_cover, drainage_grate, pavement_patch
VERTICAL FEATURES (above ground): traffic_sign, street_light, utility_pole, trash_bin, fire_hydrant, traffic_light, vegetation

Conditions: good, fair, poor, damaged"""

        # Start with system prompt + conversation history
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add conversation history (keep last 10 messages for context)
        messages.extend(self.conversation_history[-10:])
        
        # Add current question
        messages.append({"role": "user", "content": question})
        
        # Step 1: Initial LLM call
        response = self.client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            tools=MAPPING_TOOLS,
            tool_choice="auto",
            temperature=0.1
        )
        
        message = response.choices[0].message
        tool_uses = []
        map_commands = []
        
        # Step 2: Execute tool calls if any
        if message.tool_calls:
            for tool_call in message.tool_calls:
                try:
                    tool_name = tool_call.function.name
                    tool_input = json.loads(tool_call.function.arguments)
                    
                    # Execute tool
                    result = self.execute_tool(tool_name, tool_input)
                    
                    # Track tool use
                    tool_uses.append({
                        "tool": tool_name,
                        "input": tool_input,
                        "result": result
                    })
                    
                    # Extract map commands (single or multiple)
                    if "map_command" in result:
                        map_commands.append(result["map_command"])
                    if "map_commands" in result:
                        map_commands.extend(result["map_commands"])
                    
                    # Add to conversation
                    messages.append({
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [tool_call]
                    })
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": tool_name,
                        "content": json.dumps(result)
                    })
                except Exception as e:
                    # Log error but continue
                    print(f"Error executing tool {tool_call.function.name}: {str(e)}")
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": tool_call.function.name,
                        "content": json.dumps({"error": str(e)})
                    })
            
            # Step 3: Get final response with tool results
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                temperature=0.1
            )
            message = response.choices[0].message
        
        # Update conversation history (store context but keep it clean)
        # Only store user questions and simplified assistant responses
        self.conversation_history.append({"role": "user", "content": question})
        if message.content:
            # Store only the clean text response, not tool call info
            clean_response = message.content.split("<function")[0].strip()  # Remove any leaked function syntax
            if clean_response:
                self.conversation_history.append({"role": "assistant", "content": clean_response})
        
        return {
            "answer": message.content or "I've updated the map.",
            "tool_uses": tool_uses,
            "map_commands": map_commands,
            "tokens": response.usage.total_tokens if response.usage else 0
        }
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []

