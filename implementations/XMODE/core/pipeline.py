import getpass
import os
import pathlib
import ast

import itertools
from langchain_openai import ChatOpenAI

# Imported from the https://github.com/langchain-ai/langgraph/tree/main/examples/plan-and-execute repo

# from langchain.sql_database import SQLDatabase
from langchain_community.utilities import SQLDatabase
from sqlalchemy import create_engine

from langchain.chains.openai_functions import create_structured_output_runnable
from langchain_core.messages import AIMessage
from pydantic import BaseModel, Field
from langgraph.graph import END, MessageGraph, START


from typing import Sequence, Dict, Optional

from langchain import hub
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import (
    BaseMessage,
    FunctionMessage,
    HumanMessage,
    SystemMessage,
)
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableBranch
from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import JsonOutputParser

import sys
# sys.path.append(os.path.dirname(os.getcwd()) + '/ceasura_langgraph')
sys.path.append(os.path.dirname(os.getcwd()))

# Fix imports to use relative imports from XMODE's src directory
from implementations.XMODE.src.joiner import *
from implementations.XMODE.src.planner import *
from implementations.XMODE.src.task_fetching_unit import *
from implementations.XMODE.src.build_graph import graph_construction
from implementations.XMODE.src.utils import *


import json

from tqdm import tqdm
from pathlib import Path


import logging



import os
import sys
# sys.path.append(os.path.dirname(os.getcwd()) + '/src')
# sys.path.append(os.path.dirname(os.getcwd()) + '/ceasura_langgraph/tools')

class Pipeline:
    def __init__(self, index_path: Optional[Path] = None, openai_api_key: Optional[str] = None, langchain_api_key: Optional[str] = None):
        self.index_path = index_path
        self.openai_api_key = openai_api_key
        self.langchain_api_key = langchain_api_key

    @staticmethod
    def _set_if_undefined(var: str):
        if not os.environ.get(var):
            os.environ[var] = getpass.getpass(f"Please provide your {var}")
            
    @staticmethod
    def pretty_print_stream_chunk(chunk):
        for node, updates in chunk.items():
            print(f"Update from node: {node}")
            if "messages" in updates:
                updates["messages"][-1].pretty_print()
            else:
                print(updates)

            print("\n")
            
    @staticmethod
    def load_json(file_path, data):
        fp = Path(file_path)
        if not fp.exists():
            fp.touch()
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=4)
        else:
            with open(file_path, 'r') as f:
                data = json.load(f)
        return data

    @staticmethod
    def append_json(data, file_path):
        fp = Path(file_path)
        if not fp.exists():
            raise FileNotFoundError(f"File {file_path} not found.")
        with open(file_path, 'r+') as f:
            _data = json.load(f)
            if type(data) == dict:
                _data.append(data)
            elif type(data) == list:
                _data.extend(data)
            else:
                raise ValueError(f"Invalid data type: {type(data)}")
            f.seek(0)
            json.dump(_data, f, ensure_ascii=False, indent=4)
        return _data

    def run_query(self, query: str):
        logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        logger = logging.getLogger(__name__)


        # _set_if_undefined("TAVILY_API_KEY")
        # # Optional, add tracing in LangSmith

        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_PROJECT"] = "XMODE-pubmed"
        
        model="gpt-4o" #gpt-4-turbo-preview
        
        
        # Use relative paths instead of hardcoded absolute paths - COME BACK TO THIS
        current_dir = os.path.dirname(os.path.abspath(__file__))
        print(f"Current directory: {current_dir}")
        # Update path to point to the data directory in the project root
        project_root = os.path.abspath(os.path.join(current_dir, "../../../"))
        db_path = os.path.join(project_root, "data/drugbank.db")
        temperature = 0
        language = 'en'
        
        # ceasura_artWork = []
        # output_path = os.path.join(current_dir, "experiments", language)
        # pathlib.Path(output_path).mkdir(parents=True, exist_ok=True) 
        # output_file = os.path.join(output_path, f'ceasura_artWork-{language}-test.json')
    
        # load_json(output_file, ceasura_artWork)
        
        results = []
        
        LOG_PATH = os.path.join(current_dir, "experiments", "log")
        pathlib.Path(LOG_PATH).mkdir(parents=True, exist_ok=True)
        
        
        # Generate a unique ID for this query
        import uuid
        query_id = str(uuid.uuid4())[:8]
        
        iddx = 1
        result={}
        result_str=''
        #logging the current use-case
        use_case_log_path = os.path.join(LOG_PATH, str(query_id))
        pathlib.Path(use_case_log_path).mkdir(parents=True, exist_ok=True) 
        for handler in logging.root.handlers:
                handler.level = logging.root.level
        file_handler = logging.FileHandler(os.path.join(use_case_log_path, 'out.log'))
        logging.root.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        logging.root.addHandler(file_handler)
        logger.debug(f"Question: {query}")
        
        result["question"]=query
        result["id"]=query_id
        print(f"Running graph construction")
        chain = graph_construction(model,temperature=temperature, db_path=db_path,log_path=use_case_log_path)
        # steps=[]
        
        
        config = {"configurable": {"thread_id": "2"}}
        
        
        
        for step in chain.stream(query, config, stream_mode="values"):
            print(step)
            # for k,v in step.items():
            #     print(k)
            #     print("---------------------")
            #     for ctx in v:
            #         print (ctx)
            result_str += f"Step {iddx:}\n {step}\n\n"
            iddx+=1
            print("---------------------")
        
        to_json=[]
        try:
            for msg in step:
                value= msg.to_json()['kwargs']
                to_json.append(value)
                # needs code or prompt imporvements
            prediction=[ast.literal_eval(step[-1].content)]
        except Exception as e:
            print(str(e)) # comes basicly from ast.literal_eval becuase the output sometimes not in JSON structure
            prediction= step[-1].content
        
        result["xmode"] = to_json
        result["prediction"]= prediction
        
        print("Result (to json): ", result["xmode"])
        print("Result (prediction): ", result["prediction"])
        
        # Format the result to match what main.py expects
        formatted_result = {}
        
        # Convert the prediction to a string regardless of its original type
        pred_str = str(prediction)
        if isinstance(prediction, list) and len(prediction) > 0:
            pred_str = str(prediction[0])
        
        # Use regex to extract the Summary and details directly from the string
        import re
        
        # Extract Summary
        summary_match = re.search(r"'Summary':\s*'([^']*)'", pred_str)
        summary = summary_match.group(1) if summary_match else ""
        
        # Extract details
        details_match = re.search(r"'details':\s*'([^']*)'", pred_str)
        details = details_match.group(1) if details_match else ""
        
        # Combine summary and details
        answer_parts = []
        if summary:
            answer_parts.append(summary)
        if details:
            answer_parts.append(details)
            
        if answer_parts:
            formatted_result["answer"] = "\n\n".join(answer_parts)
        else:
            # If we couldn't extract either summary or details, use the whole output
            formatted_result["answer"] = pred_str
        
        # Extract source information if available
        source_match = re.search(r"'source':\s*'([^']*)'", pred_str)
        if source_match:
            source_str = source_match.group(1)
            formatted_result["document_sources"] = [src.strip() for src in source_str.split(',')]
        else:
            formatted_result["document_sources"] = []
        
        # Check for tables_used in the last message content
        if isinstance(step, list) and len(step) > 0:
            last_message = step[-1]
            if hasattr(last_message, 'content') and 'Tables used in this query:' in last_message.content:
                # Extract tables from the message
                content = last_message.content
                tables_part = content.split('Tables used in this query:')[-1].strip()
                tables = [table.strip() for table in tables_part.split(',')]
                formatted_result["document_sources"] = tables
        
        # If we still don't have document sources, try to get from additional_kwargs
        if not formatted_result["document_sources"]:
            for msg in to_json:
                if isinstance(msg, dict) and msg.get('additional_kwargs') and 'tables_used' in msg['additional_kwargs']:
                    formatted_result["document_sources"] = msg['additional_kwargs']['tables_used']
                    break
                    
        print("Formatted answer:", formatted_result["answer"])
        
        path = os.path.join(use_case_log_path, "steps-values.log")
        with open(path, "w") as f: 
            print(result_str, file=f)
        
        # append_json(results,output_file)
    
        # all_states = []
        # for state in chain.get_state(config):
        #    print(state) 
        # it is better to creat graph for each question
        
        return formatted_result