# -*- coding: utf-8 -*-

from cgitb import handler
import logging
import ask_sdk_core.utils as ask_utils
import moviesearch as search
import sys

from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.dispatch_components import AbstractExceptionHandler
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_model import Response

# APL imports
import json
import apl_content as apl
from ask_sdk_core.utils import get_supported_interfaces
from ask_sdk_model.interfaces.alexa.presentation.apl import (
    RenderDocumentDirective)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


# ----------------------------------------------------------------------
class LaunchRequestHandler(AbstractRequestHandler):
    """Handler for Skill Launch."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool

        return ask_utils.is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        logger.info('--- Version info:')
        logger.info(sys.version_info)

        speak_output = 'Welcome, you can say Tell me about new movies or'\
                       'Help. Which would you like to try?'
        response_builder = handler_input.response_builder

        if get_supported_interfaces(
                        handler_input).alexa_presentation_apl is not None:
            response_builder.add_directive(
                RenderDocumentDirective(
                    token=apl.MOVIES_TOKEN,
                    document=apl._load_apl_document(apl.APL_DOC['launch']),
                    datasources=search.MovieSearch().get_apl_launch()
                )
            )

        return (
            response_builder
            .speak(speak_output)
            .ask(speak_output)
            .response
        )


# ----------------------------------------------------------------------
class MovieInfoIntentHandler(AbstractRequestHandler):
    """Handler for Movie Info Intent."""

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("MovieInfoIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = ('Sorry but would you mind repeating your '
                        'request again, please?')

        slots = handler_input.request_envelope.request.intent.slots
        movie_name = slots["movie_name"].value
        if (movie_name is not None):
            movies = search.MovieSearch()
            if (movies.movie_info(movie_name) is True):
                num_movies = movies.num_movies()
                if (num_movies > 0):
                    if get_supported_interfaces(
                            handler_input).alexa_presentation_apl is not None:
                        handler_input.response_builder.add_directive(
                            RenderDocumentDirective(
                                token=apl.MOVIES_TOKEN,
                                document=apl._load_apl_document(
                                    apl.APL_DOC['movie_detail']),
                                datasources=movies.get_apl_movies_detail()
                            )
                        )
                    if (num_movies > 1):
                        speak_output = ('I found information about'
                                        f'{num_movies} movies:')
                    else:
                        speak_output = ''
                    for m in movies.movies.values():
                        speak_output += ('<break strength="x-strong"/>Plot'
                                         ' summary for the movie ' + m.title)
                        speak_output += ('<break strength="strong"/>'
                                         + m.overview)
                else:
                    speak_output = ('I couldn\'t find any information about'
                                    f' the movie {movie_name}')

        logger.info('### MovieInfoIntentHandler')
        logger.info(speak_output)

        return (
            handler_input.response_builder
            .speak(speak_output)
            # .ask("add a reprompt if you want to keep the session open")
            .response
        )


# ----------------------------------------------------------------------
class NewMoviesIntentHandler(AbstractRequestHandler):
    """Handler for New Movies Intent."""

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("NewMoviesIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response

        speak_output = ('Sorry but would you mind repeating your request'
                        ' again, please?')
        response_builder = handler_input.response_builder

        slots = handler_input.request_envelope.request.intent.slots
        text_week = slots["week_type"].value
        week_type = search.get_week_from_text(text_week)
        if (week_type is not None):
            movies = search.MovieSearch()
            if (movies.released_in_week(week_type) is True):
                if get_supported_interfaces(
                        handler_input).alexa_presentation_apl is not None:
                    response_builder.add_directive(
                        RenderDocumentDirective(
                            token=apl.MOVIES_TOKEN,
                            document=apl._load_apl_document(
                                apl.APL_DOC['movie_list']),
                            datasources=movies.get_apl_movies_list()
                        )
                    )

                if (movies.num_movies() > 0):
                    speak_output = (f'The new movies released {text_week}'
                                    ' week are:')
                    for m in movies.movies.values():
                        speak_output += '<break strength="strong"/>' + m.title
                else:
                    speak_output = ('There are no new movies released'
                                    f' {text_week} week.')

        return (
            response_builder
            .speak(speak_output)
            # .ask("add a reprompt if you want to keep the session open")
            .response
        )


# ----------------------------------------------------------------------
class HelpIntentHandler(AbstractRequestHandler):
    """Handler for Help Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = ('You can ask me to tell you which new movies have been'
                        ' released this week, last week or next week. For'
                        ' example: tell me about new movies this week')
        speak_output += ('You can also ask me to tell you about a particular'
                         ' movie name. For example: tell me about the movie'
                         ' Jack Reacher')
        return (
            handler_input.response_builder
            .speak(speak_output)
            .ask(speak_output)
            .response
        )


# ----------------------------------------------------------------------
class CancelOrStopIntentHandler(AbstractRequestHandler):
    """Single handler for Cancel and Stop Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return (
            ask_utils.is_intent_name("AMAZON.CancelIntent")(handler_input) or
            ask_utils.is_intent_name("AMAZON.StopIntent")(handler_input))

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "Goodbye!"

        return (
            handler_input.response_builder
            .speak(speak_output)
            .response
        )


# ----------------------------------------------------------------------
class SessionEndedRequestHandler(AbstractRequestHandler):
    """Handler for Session End."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response

        # Any cleanup logic goes here.

        return handler_input.response_builder.response


# ----------------------------------------------------------------------
class IntentReflectorHandler(AbstractRequestHandler):
    """ The intent reflector is used for interaction model testing and
    debugging. It will simply repeat the intent the user said. You can
    create custom handlers for your intents by defining them above, then
    also adding them to the request handler chain below.
    """
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("IntentRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        intent_name = ask_utils.get_intent_name(handler_input)
        speak_output = "You just triggered " + intent_name + "."

        return (
            handler_input.response_builder
            .speak(speak_output)
            # .ask("add a reprompt if you want to keep the session open")
            .response
        )


# ----------------------------------------------------------------------
class CatchAllExceptionHandler(AbstractExceptionHandler):
    """Generic error handling to capture any syntax or routing errors. If you
    receive an error stating the request handler chain is not found, you have
    not implemented a handler for the intent being invoked or included it in
    the skill builder below.
    """
    def can_handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> bool
        return True

    def handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> Response
        logger.error(exception, exc_info=True)

        speak_output = ('Sorry, I had trouble doing what you asked.'
                        ' Please try again.')

        return (
            handler_input.response_builder
            .speak(speak_output)
            .ask(speak_output)
            .response
        )


"""
The SkillBuilder object acts as the entry point for your skill, routing all
request and response payloads to the handlers above. Make sure any new
handlers or interceptors you've defined are included below.
The order matters - they're processed top to bottom.
"""

sb = SkillBuilder()

sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(NewMoviesIntentHandler())
sb.add_request_handler(MovieInfoIntentHandler())
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())
# make sure IntentReflectorHandler is last - don't override custom handlers
sb.add_request_handler(IntentReflectorHandler())

sb.add_exception_handler(CatchAllExceptionHandler())

lambda_handler = sb.lambda_handler()
