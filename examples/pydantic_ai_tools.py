from pydantic_ai import RunContext


def register_tools(agent):
    """Register all tools with the agent"""

    @agent.add_custom_tool
    async def get_weather(ctx: RunContext[None], location: str) -> dict:
        """
        Get current weather information for a location

        Args:
            location: The city or location to get weather for

        Returns:
            WeatherData: Weather information for the location
        """
        # Simulate weather API call (replace with real API)
        weather_data = {
            "New York": {"temp": 22.5, "desc": "Partly cloudy", "humidity": 65},
            "London": {"temp": 15.0, "desc": "Rainy", "humidity": 80},
            "Tokyo": {"temp": 28.0, "desc": "Sunny", "humidity": 55},
        }

        data = weather_data.get(
            location,
            {
                "temp": 20.0,
                "desc": "Unknown location - showing default weather",
                "humidity": 60,
            },
        )

        return {
            "location": location,
            "temperature": data["temp"],
            "description": data["desc"],
            "humidity": data["humidity"],
        }

    @agent.add_custom_tool
    def calculate(ctx: RunContext[None], expression: str) -> float:
        """
        Safely evaluate mathematical expressions

        Args:
            expression: Mathematical expression to evaluate (e.g., "2 + 3 * 4")

        Returns:
            float: Result of the calculation
        """
        try:
            # Only allow basic mathematical operations for safety
            allowed_chars = set("0123456789+-*/.() ")
            if not all(c in allowed_chars for c in expression):
                raise ValueError("Invalid characters in expression")

            result = eval(expression)
            return float(result)
        except Exception as e:
            raise ValueError(f"Calculation error: {str(e)}")

    @agent.add_custom_tool
    async def search_web(ctx: RunContext[None], query: str) -> str:
        """
        Simulate a web search (replace with real search API)

        Args:
            query: Search query string

        Returns:
            str: Search results summary
        """
        # This is a mock implementation - replace with real search API
        mock_results = {
            "python": "Python is a high-level programming language known for its simplicity and readability.",
            "ai": "Artificial Intelligence is the simulation of human intelligence in machines.",
            "weather": "Weather refers to atmospheric conditions at a specific time and place.",
        }

        for key, value in mock_results.items():
            if key.lower() in query.lower():
                return f"Search results for '{query}': {value}"

        return f"Search results for '{query}': No specific information found in mock database."
