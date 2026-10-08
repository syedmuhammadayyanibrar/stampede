# Stampede Live API Reference

The Stampede API provides real-time pricing, risk valuation, contract sizing, and secondary market evaluation for forward AI inference capacity.

## Core Route Inventory

| Route Name | Endpoint Path | Method | Status | Notes |
|---|---|:---:|:---:|---|
| **evidence** | `/api/v1/sessions/{session_id}/evidence/{prompt_idx}` | GET | **EXISTS** | Inspection drawer outputs, check results & verdicts |
| **DELETE session** | `/api/v1/sessions/{session_id}` | DELETE | **EXISTS** | Immediate wipe of memory, draws, and cache |
| **models** | `/api/v1/models` | GET | **EXISTS** | Catalog listing of candidates and incumbents |
| **budget** | `/budget` & `/api/v1/budget` | GET | **EXISTS** | Session and global spend limits and ledgers |
| **explain** | `/api/v1/sessions/{session_id}/explain` | POST | **EXISTS** | Exact 5-factor Shapley attribution on plan/quote |
| **load-sample** | `/api/v1/sessions/{session_id}/load-sample` | POST | **EXISTS** | Instant zero-spend benchmark replay |
| **seller/uplift** | `/seller/uplift` & `/api/v1/seller/uplift` | POST | **EXISTS** | 100 LHS draws for provider utilization uplift |

## Complete Endpoints Directory

| Path | Method | Operation ID | Summary |
|---|---|---|---|
| `/api/copilot/fit-check` | **POST** | `api_fit_check_api_copilot_fit_check_post` | Api Fit Check |
| `/api/copilot/parse` | **POST** | `api_parse_csv_api_copilot_parse_post` | Api Parse Csv |
| `/api/copilot/run` | **POST** | `api_copilot_run_api_copilot_run_post` | Api Copilot Run |
| `/api/crunch/data-driven` | **GET** | `api_crunch_comparison_api_crunch_data_driven_get` | Api Crunch Comparison |
| `/api/data` | **GET** | `get_site_data_api_data_get` | Get Site Data |
| `/api/health` | **GET** | `health_api_health_get` | Health |
| `/api/migration/dataset` | **GET** | `api_migration_api_migration_dataset_get` | Api Migration |
| `/api/v1/budget` | **GET** | `get_budget_endpoint_api_v1_budget_get` | Get Budget Endpoint |
| `/api/v1/models` | **GET** | `list_models_api_v1_models_get` | List Models |
| `/api/v1/seller/uplift` | **POST** | `seller_uplift_endpoint_api_v1_seller_uplift_post` | Seller Uplift Endpoint |
| `/api/v1/sessions` | **POST** | `create_session_api_v1_sessions_post` | Create Session |
| `/api/v1/sessions/{session_id}` | **DELETE** | `delete_session_api_v1_sessions__session_id__delete` | Delete Session |
| `/api/v1/sessions/{session_id}` | **GET** | `get_session_api_v1_sessions__session_id__get` | Get Session |
| `/api/v1/sessions/{session_id}/constraints` | **GET** | `get_constraints_endpoint_api_v1_sessions__session_id__constraints_get` | Get Constraints Endpoint |
| `/api/v1/sessions/{session_id}/constraints` | **PUT** | `update_constraints_endpoint_api_v1_sessions__session_id__constraints_put` | Update Constraints Endpoint |
| `/api/v1/sessions/{session_id}/constraints/parse` | **POST** | `parse_constraints_endpoint_api_v1_sessions__session_id__constraints_parse_post` | Parse Constraints Endpoint |
| `/api/v1/sessions/{session_id}/constraints/structured` | **PUT** | `update_structured_constraints_endpoint_api_v1_sessions__session_id__constraints_structured_put` | Update Structured Constraints Endpoint |
| `/api/v1/sessions/{session_id}/estimate` | **POST** | `get_session_estimate_api_v1_sessions__session_id__estimate_post` | Get Session Estimate |
| `/api/v1/sessions/{session_id}/events` | **GET** | `get_events_api_v1_sessions__session_id__events_get` | Get Events |
| `/api/v1/sessions/{session_id}/evidence` | **GET** | `list_session_evidence_api_v1_sessions__session_id__evidence_get` | List Session Evidence |
| `/api/v1/sessions/{session_id}/evidence/{prompt_idx}` | **GET** | `get_evidence_item_api_v1_sessions__session_id__evidence__prompt_idx__get` | Get Evidence Item |
| `/api/v1/sessions/{session_id}/explain` | **POST** | `explain_endpoint_api_v1_sessions__session_id__explain_post` | Explain Endpoint |
| `/api/v1/sessions/{session_id}/inputs` | **POST** | `update_inputs_api_v1_sessions__session_id__inputs_post` | Update Inputs |
| `/api/v1/sessions/{session_id}/load-sample` | **POST** | `load_sample_endpoint_api_v1_sessions__session_id__load_sample_post` | Load Sample Endpoint |
| `/api/v1/sessions/{session_id}/plan` | **GET** | `get_plan_endpoint_api_v1_sessions__session_id__plan_get` | Get Plan Endpoint |
| `/api/v1/sessions/{session_id}/quotes` | **PUT** | `update_quotes_endpoint_api_v1_sessions__session_id__quotes_put` | Update Quotes Endpoint |
| `/api/v1/sessions/{session_id}/quotes/parse` | **POST** | `parse_quotes_endpoint_api_v1_sessions__session_id__quotes_parse_post` | Parse Quotes Endpoint |
| `/api/v1/sessions/{session_id}/reservation-prices` | **GET** | `get_reservation_prices_endpoint_api_v1_sessions__session_id__reservation_prices_get` | Get Reservation Prices Endpoint |
| `/api/v1/sessions/{session_id}/results` | **GET** | `get_results_api_v1_sessions__session_id__results_get` | Get Results |
| `/api/v1/sessions/{session_id}/rfq/render` | **POST** | `render_rfq_endpoint_api_v1_sessions__session_id__rfq_render_post` | Render Rfq Endpoint |
| `/api/v1/sessions/{session_id}/run` | **POST** | `trigger_run_api_v1_sessions__session_id__run_post` | Trigger Run |
| `/api/v1/sessions/{session_id}/usage` | **PUT** | `update_usage_endpoint_api_v1_sessions__session_id__usage_put` | Update Usage Endpoint |
| `/api/v1/sessions/{session_id}/waterfall` | **GET** | `get_waterfall_endpoint_api_v1_sessions__session_id__waterfall_get` | Get Waterfall Endpoint |
| `/api/v1/sessions/{session_id}/whatif` | **POST** | `whatif_endpoint_api_v1_sessions__session_id__whatif_post` | Whatif Endpoint |
| `/api/v1/sessions/{session_id}/workload` | **PUT** | `update_workload_endpoint_api_v1_sessions__session_id__workload_put` | Update Workload Endpoint |
| `/budget` | **GET** | `root_budget_budget_get` | Root Budget |
| `/seller/uplift` | **POST** | `root_seller_uplift_seller_uplift_post` | Root Seller Uplift |


## OpenAPI 3.1.0 Specification Dump

```json
{
  "openapi": "3.1.0",
  "info": {
    "title": "Stampede Risk Engine & Contract API",
    "version": "0.1.0"
  },
  "paths": {
    "/api/v1/sessions": {
      "post": {
        "summary": "Create Session",
        "operationId": "create_session_api_v1_sessions_post",
        "requestBody": {
          "content": {
            "application/json": {
              "schema": {
                "anyOf": [
                  {
                    "additionalProperties": true,
                    "type": "object"
                  },
                  {
                    "type": "null"
                  }
                ],
                "title": "Body"
              }
            }
          }
        },
        "responses": {
          "200": {
            "description": "Successful Response",
            "content": {
              "application/json": {
                "schema": {}
              }
            }
          },
          "422": {
            "description": "Validation Error",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            }
          }
        }
      }
    },
    "/api/v1/sessions/{session_id}": {
      "get": {
        "summary": "Get Session",
        "operationId": "get_session_api_v1_sessions__session_id__get",
        "parameters": [
          {
            "name": "session_id",
            "in": "path",
            "required": true,
            "schema": {
              "type": "string",
              "title": "Session Id"
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Successful Response",
            "content": {
              "application/json": {
                "schema": {}
              }
            }
          },
          "422": {
            "description": "Validation Error",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            }
          }
        }
      },
      "delete": {
        "summary": "Delete Session",
        "operationId": "delete_session_api_v1_sessions__session_id__delete",
        "parameters": [
          {
            "name": "session_id",
            "in": "path",
            "required": true,
            "schema": {
              "type": "string",
              "title": "Session Id"
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Successful Response",
            "content": {
              "application/json": {
                "schema": {}
              }
            }
          },
          "422": {
            "description": "Validation Error",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            }
          }
        }
      }
    },
    "/api/v1/sessions/{session_id}/inputs": {
      "post": {
        "summary": "Update Inputs",
        "operationId": "update_inputs_api_v1_sessions__session_id__inputs_post",
        "parameters": [
          {
            "name": "session_id",
            "in": "path",
            "required": true,
            "schema": {
              "type": "string",
              "title": "Session Id"
            }
          }
        ],
        "requestBody": {
          "required": true,
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "additionalProperties": true,
                "title": "Payload"
              }
            }
          }
        },
        "responses": {
          "200": {
            "description": "Successful Response",
            "content": {
              "application/json": {
                "schema": {}
              }
            }
          },
          "422": {
            "description": "Validation Error",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            }
          }
        }
      }
    },
    "/api/v1/sessions/{session_id}/usage": {
      "put": {
        "summary": "Update Usage Endpoint",
        "operationId": "update_usage_endpoint_api_v1_sessions__session_id__usage_put",
        "parameters": [
          {
            "name": "session_id",
            "in": "path",
            "required": true,
            "schema": {
              "type": "string",
              "title": "Session Id"
            }
          }
        ],
        "requestBody": {
          "required": true,
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "additionalProperties": true,
                "title": "Body"
              }
            }
          }
        },
        "responses": {
          "200": {
            "description": "Successful Response",
            "content": {
              "application/json": {
                "schema": {}
              }
            }
          },
          "422": {
            "description": "Validation Error",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            }
          }
        }
      }
    },
    "/api/v1/sessions/{session_id}/workload": {
      "put": {
        "summary": "Update Workload Endpoint",
        "operationId": "update_workload_endpoint_api_v1_sessions__session_id__workload_put",
        "parameters": [
          {
            "name": "session_id",
            "in": "path",
            "required": true,
            "schema": {
              "type": "string",
              "title": "Session Id"
            }
          }
        ],
        "requestBody": {
          "required": true,
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "additionalProperties": true,
                "title": "Body"
              }
            }
          }
        },
        "responses": {
          "200": {
            "description": "Successful Response",
            "content": {
              "application/json": {
                "schema": {}
              }
            }
          },
          "422": {
            "description": "Validation Error",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            }
          }
        }
      }
    },
    "/api/v1/sessions/{session_id}/quotes": {
      "put": {
        "summary": "Update Quotes Endpoint",
        "operationId": "update_quotes_endpoint_api_v1_sessions__session_id__quotes_put",
        "parameters": [
          {
            "name": "session_id",
            "in": "path",
            "required": true,
            "schema": {
              "type": "string",
              "title": "Session Id"
            }
          }
        ],
        "requestBody": {
          "required": true,
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "additionalProperties": true,
                "title": "Body"
              }
            }
          }
        },
        "responses": {
          "200": {
            "description": "Successful Response",
            "content": {
              "application/json": {
                "schema": {}
              }
            }
          },
          "422": {
            "description": "Validation Error",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            }
          }
        }
      }
    },
    "/api/v1/sessions/{session_id}/load-sample": {
      "post": {
        "summary": "Load Sample Endpoint",
        "operationId": "load_sample_endpoint_api_v1_sessions__session_id__load_sample_post",
        "parameters": [
          {
            "name": "session_id",
            "in": "path",
            "required": true,
            "schema": {
              "type": "string",
              "title": "Session Id"
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Successful Response",
            "content": {
              "application/json": {
                "schema": {}
              }
            }
          },
          "422": {
            "description": "Validation Error",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            }
          }
        }
      }
    },
    "/api/v1/sessions/{session_id}/estimate": {
      "post": {
        "summary": "Get Session Estimate",
        "operationId": "get_session_estimate_api_v1_sessions__session_id__estimate_post",
        "parameters": [
          {
            "name": "session_id",
            "in": "path",
            "required": true,
            "schema": {
              "type": "string",
              "title": "Session Id"
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Successful Response",
            "content": {
              "application/json": {
                "schema": {}
              }
            }
          },
          "422": {
            "description": "Validation Error",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            }
          }
        }
      }
    },
    "/api/v1/sessions/{session_id}/run": {
      "post": {
        "summary": "Trigger Run",
        "operationId": "trigger_run_api_v1_sessions__session_id__run_post",
        "parameters": [
          {
            "name": "session_id",
            "in": "path",
            "required": true,
            "schema": {
              "type": "string",
              "title": "Session Id"
            }
          },
          {
            "name": "X-Provider-Key",
            "in": "header",
            "required": false,
            "schema": {
              "anyOf": [
                {
                  "type": "string"
                },
                {
                  "type": "null"
                }
              ],
              "title": "X-Provider-Key"
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Successful Response",
            "content": {
              "application/json": {
                "schema": {}
              }
            }
          },
          "422": {
            "description": "Validation Error",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            }
          }
        }
      }
    },
    "/api/v1/sessions/{session_id}/events": {
      "get": {
        "summary": "Get Events",
        "operationId": "get_events_api_v1_sessions__session_id__events_get",
        "parameters": [
          {
            "name": "session_id",
            "in": "path",
            "required": true,
            "schema": {
              "type": "string",
              "title": "Session Id"
            }
          },
          {
            "name": "Last-Event-ID",
            "in": "header",
            "required": false,
            "schema": {
              "anyOf": [
                {
                  "type": "string"
                },
                {
                  "type": "null"
                }
              ],
              "title": "Last-Event-Id"
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Successful Response",
            "content": {
              "application/json": {
                "schema": {}
              }
            }
          },
          "422": {
            "description": "Validation Error",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            }
          }
        }
      }
    },
    "/api/v1/sessions/{session_id}/results": {
      "get": {
        "summary": "Get Results",
        "operationId": "get_results_api_v1_sessions__session_id__results_get",
        "parameters": [
          {
            "name": "session_id",
            "in": "path",
            "required": true,
            "schema": {
              "type": "string",
              "title": "Session Id"
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Successful Response",
            "content": {
              "application/json": {
                "schema": {}
              }
            }
          },
          "422": {
            "description": "Validation Error",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            }
          }
        }
      }
    },
    "/api/v1/sessions/{session_id}/evidence/{prompt_idx}": {
      "get": {
        "summary": "Get Evidence Item",
        "operationId": "get_evidence_item_api_v1_sessions__session_id__evidence__prompt_idx__get",
        "parameters": [
          {
            "name": "session_id",
            "in": "path",
            "required": true,
            "schema": {
              "type": "string",
              "title": "Session Id"
            }
          },
          {
            "name": "prompt_idx",
            "in": "path",
            "required": true,
            "schema": {
              "type": "integer",
              "title": "Prompt Idx"
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Successful Response",
            "content": {
              "application/json": {
                "schema": {}
              }
            }
          },
          "422": {
            "description": "Validation Error",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            }
          }
        }
      }
    },
    "/api/v1/sessions/{session_id}/evidence": {
      "get": {
        "summary": "List Session Evidence",
        "operationId": "list_session_evidence_api_v1_sessions__session_id__evidence_get",
        "parameters": [
          {
            "name": "session_id",
            "in": "path",
            "required": true,
            "schema": {
              "type": "string",
              "title": "Session Id"
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Successful Response",
            "content": {
              "application/json": {
                "schema": {}
              }
            }
          },
          "422": {
            "description": "Validation Error",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            }
          }
        }
      }
    },
    "/api/v1/sessions/{session_id}/reservation-prices": {
      "get": {
        "summary": "Get Reservation Prices Endpoint",
        "operationId": "get_reservation_prices_endpoint_api_v1_sessions__session_id__reservation_prices_get",
        "parameters": [
          {
            "name": "session_id",
            "in": "path",
            "required": true,
            "schema": {
              "type": "string",
              "title": "Session Id"
            }
          },
          {
            "name": "rho",
            "in": "query",
            "required": false,
            "schema": {
              "type": "number",
              "default": 0.5,
              "title": "Rho"
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Successful Response",
            "content": {
              "application/json": {
                "schema": {}
              }
            }
          },
          "422": {
            "description": "Validation Error",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            }
          }
        }
      }
    },
    "/api/v1/sessions/{session_id}/waterfall": {
      "get": {
        "summary": "Get Waterfall Endpoint",
        "operationId": "get_waterfall_endpoint_api_v1_sessions__session_id__waterfall_get",
        "parameters": [
          {
            "name": "session_id",
            "in": "path",
            "required": true,
            "schema": {
              "type": "string",
              "title": "Session Id"
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Successful Response",
            "content": {
              "application/json": {
                "schema": {}
              }
            }
          },
          "422": {
            "description": "Validation Error",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            }
          }
        }
      }
    },
    "/api/v1/sessions/{session_id}/whatif": {
      "post": {
        "summary": "Whatif Endpoint",
        "operationId": "whatif_endpoint_api_v1_sessions__session_id__whatif_post",
        "parameters": [
          {
            "name": "session_id",
            "in": "path",
            "required": true,
            "schema": {
              "type": "string",
              "title": "Session Id"
            }
          }
        ],
        "requestBody": {
          "content": {
            "application/json": {
              "schema": {
                "anyOf": [
                  {
                    "type": "object",
                    "additionalProperties": true
                  },
                  {
                    "type": "null"
                  }
                ],
                "title": "Overrides"
              }
            }
          }
        },
        "responses": {
          "200": {
            "description": "Successful Response",
            "content": {
              "application/json": {
                "schema": {}
              }
            }
          },
          "422": {
            "description": "Validation Error",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            }
          }
        }
      }
    },
    "/api/v1/sessions/{session_id}/constraints/parse": {
      "post": {
        "summary": "Parse Constraints Endpoint",
        "operationId": "parse_constraints_endpoint_api_v1_sessions__session_id__constraints_parse_post",
        "parameters": [
          {
            "name": "session_id",
            "in": "path",
            "required": true,
            "schema": {
              "type": "string",
              "title": "Session Id"
            }
          }
        ],
        "requestBody": {
          "required": true,
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "additionalProperties": {
                  "type": "string"
                },
                "title": "Body"
              }
            }
          }
        },
        "responses": {
          "200": {
            "description": "Successful Response",
            "content": {
              "application/json": {
                "schema": {}
              }
            }
          },
          "422": {
            "description": "Validation Error",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            }
          }
        }
      }
    },
    "/api/v1/sessions/{session_id}/constraints": {
      "put": {
        "summary": "Update Constraints Endpoint",
        "operationId": "update_constraints_endpoint_api_v1_sessions__session_id__constraints_put",
        "parameters": [
          {
            "name": "session_id",
            "in": "path",
            "required": true,
            "schema": {
              "type": "string",
              "title": "Session Id"
            }
          }
        ],
        "requestBody": {
          "required": true,
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "additionalProperties": {
                  "type": "string"
                },
                "title": "Body"
              }
            }
          }
        },
        "responses": {
          "200": {
            "description": "Successful Response",
            "content": {
              "application/json": {
                "schema": {}
              }
            }
          },
          "422": {
            "description": "Validation Error",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            }
          }
        }
      },
      "get": {
        "summary": "Get Constraints Endpoint",
        "operationId": "get_constraints_endpoint_api_v1_sessions__session_id__constraints_get",
        "parameters": [
          {
            "name": "session_id",
            "in": "path",
            "required": true,
            "schema": {
              "type": "string",
              "title": "Session Id"
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Successful Response",
            "content": {
              "application/json": {
                "schema": {}
              }
            }
          },
          "422": {
            "description": "Validation Error",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            }
          }
        }
      }
    },
    "/api/v1/sessions/{session_id}/constraints/structured": {
      "put": {
        "summary": "Update Structured Constraints Endpoint",
        "operationId": "update_structured_constraints_endpoint_api_v1_sessions__session_id__constraints_structured_put",
        "parameters": [
          {
            "name": "session_id",
            "in": "path",
            "required": true,
            "schema": {
              "type": "string",
              "title": "Session Id"
            }
          }
        ],
        "requestBody": {
          "required": true,
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "additionalProperties": true,
                "title": "Body"
              }
            }
          }
        },
        "responses": {
          "200": {
            "description": "Successful Response",
            "content": {
              "application/json": {
                "schema": {}
              }
            }
          },
          "422": {
            "description": "Validation Error",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            }
          }
        }
      }
    },
    "/api/v1/sessions/{session_id}/plan": {
      "get": {
        "summary": "Get Plan Endpoint",
        "operationId": "get_plan_endpoint_api_v1_sessions__session_id__plan_get",
        "parameters": [
          {
            "name": "session_id",
            "in": "path",
            "required": true,
            "schema": {
              "type": "string",
              "title": "Session Id"
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Successful Response",
            "content": {
              "application/json": {
                "schema": {}
              }
            }
          },
          "422": {
            "description": "Validation Error",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            }
          }
        }
      }
    },
    "/api/v1/sessions/{session_id}/quotes/parse": {
      "post": {
        "summary": "Parse Quotes Endpoint",
        "operationId": "parse_quotes_endpoint_api_v1_sessions__session_id__quotes_parse_post",
        "parameters": [
          {
            "name": "session_id",
            "in": "path",
            "required": true,
            "schema": {
              "type": "string",
              "title": "Session Id"
            }
          }
        ],
        "requestBody": {
          "required": true,
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "additionalProperties": {
                  "type": "string"
                },
                "title": "Body"
              }
            }
          }
        },
        "responses": {
          "200": {
            "description": "Successful Response",
            "content": {
              "application/json": {
                "schema": {}
              }
            }
          },
          "422": {
            "description": "Validation Error",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            }
          }
        }
      }
    },
    "/api/v1/sessions/{session_id}/rfq/render": {
      "post": {
        "summary": "Render Rfq Endpoint",
        "operationId": "render_rfq_endpoint_api_v1_sessions__session_id__rfq_render_post",
        "parameters": [
          {
            "name": "session_id",
            "in": "path",
            "required": true,
            "schema": {
              "type": "string",
              "title": "Session Id"
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Successful Response",
            "content": {
              "application/json": {
                "schema": {}
              }
            }
          },
          "422": {
            "description": "Validation Error",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            }
          }
        }
      }
    },
    "/api/v1/models": {
      "get": {
        "summary": "List Models",
        "operationId": "list_models_api_v1_models_get",
        "responses": {
          "200": {
            "description": "Successful Response",
            "content": {
              "application/json": {
                "schema": {}
              }
            }
          }
        }
      }
    },
    "/api/v1/budget": {
      "get": {
        "summary": "Get Budget Endpoint",
        "operationId": "get_budget_endpoint_api_v1_budget_get",
        "responses": {
          "200": {
            "description": "Successful Response",
            "content": {
              "application/json": {
                "schema": {}
              }
            }
          }
        }
      }
    },
    "/api/v1/seller/uplift": {
      "post": {
        "summary": "Seller Uplift Endpoint",
        "operationId": "seller_uplift_endpoint_api_v1_seller_uplift_post",
        "requestBody": {
          "content": {
            "application/json": {
              "schema": {
                "anyOf": [
                  {
                    "additionalProperties": true,
                    "type": "object"
                  },
                  {
                    "type": "null"
                  }
                ],
                "title": "Body"
              }
            }
          }
        },
        "responses": {
          "200": {
            "description": "Successful Response",
            "content": {
              "application/json": {
                "schema": {}
              }
            }
          },
          "422": {
            "description": "Validation Error",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            }
          }
        }
      }
    },
    "/api/v1/sessions/{session_id}/explain": {
      "post": {
        "summary": "Explain Endpoint",
        "operationId": "explain_endpoint_api_v1_sessions__session_id__explain_post",
        "parameters": [
          {
            "name": "session_id",
            "in": "path",
            "required": true,
            "schema": {
              "type": "string",
              "title": "Session Id"
            }
          }
        ],
        "requestBody": {
          "content": {
            "application/json": {
              "schema": {
                "anyOf": [
                  {
                    "type": "object",
                    "additionalProperties": true
                  },
                  {
                    "type": "null"
                  }
                ],
                "title": "Body"
              }
            }
          }
        },
        "responses": {
          "200": {
            "description": "Successful Response",
            "content": {
              "application/json": {
                "schema": {}
              }
            }
          },
          "422": {
            "description": "Validation Error",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            }
          }
        }
      }
    },
    "/api/health": {
      "get": {
        "summary": "Health",
        "operationId": "health_api_health_get",
        "responses": {
          "200": {
            "description": "Successful Response",
            "content": {
              "application/json": {
                "schema": {}
              }
            }
          }
        }
      }
    },
    "/budget": {
      "get": {
        "summary": "Root Budget",
        "operationId": "root_budget_budget_get",
        "responses": {
          "200": {
            "description": "Successful Response",
            "content": {
              "application/json": {
                "schema": {}
              }
            }
          }
        }
      }
    },
    "/seller/uplift": {
      "post": {
        "summary": "Root Seller Uplift",
        "operationId": "root_seller_uplift_seller_uplift_post",
        "requestBody": {
          "content": {
            "application/json": {
              "schema": {
                "anyOf": [
                  {
                    "additionalProperties": true,
                    "type": "object"
                  },
                  {
                    "type": "null"
                  }
                ],
                "title": "Body"
              }
            }
          }
        },
        "responses": {
          "200": {
            "description": "Successful Response",
            "content": {
              "application/json": {
                "schema": {}
              }
            }
          },
          "422": {
            "description": "Validation Error",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            }
          }
        }
      }
    },
    "/api/data": {
      "get": {
        "summary": "Get Site Data",
        "operationId": "get_site_data_api_data_get",
        "responses": {
          "200": {
            "description": "Successful Response",
            "content": {
              "application/json": {
                "schema": {}
              }
            }
          }
        }
      }
    },
    "/api/copilot/parse": {
      "post": {
        "summary": "Api Parse Csv",
        "operationId": "api_parse_csv_api_copilot_parse_post",
        "requestBody": {
          "content": {
            "application/json": {
              "schema": {
                "$ref": "#/components/schemas/ParseRequest"
              }
            }
          },
          "required": true
        },
        "responses": {
          "200": {
            "description": "Successful Response",
            "content": {
              "application/json": {
                "schema": {}
              }
            }
          },
          "422": {
            "description": "Validation Error",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            }
          }
        }
      }
    },
    "/api/copilot/fit-check": {
      "post": {
        "summary": "Api Fit Check",
        "operationId": "api_fit_check_api_copilot_fit_check_post",
        "requestBody": {
          "content": {
            "application/json": {
              "schema": {
                "$ref": "#/components/schemas/FitCheckRequest"
              }
            }
          },
          "required": true
        },
        "responses": {
          "200": {
            "description": "Successful Response",
            "content": {
              "application/json": {
                "schema": {}
              }
            }
          },
          "422": {
            "description": "Validation Error",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            }
          }
        }
      }
    },
    "/api/copilot/run": {
      "post": {
        "summary": "Api Copilot Run",
        "operationId": "api_copilot_run_api_copilot_run_post",
        "requestBody": {
          "content": {
            "application/json": {
              "schema": {
                "$ref": "#/components/schemas/CopilotRunRequest"
              }
            }
          },
          "required": true
        },
        "responses": {
          "200": {
            "description": "Successful Response",
            "content": {
              "application/json": {
                "schema": {}
              }
            }
          },
          "422": {
            "description": "Validation Error",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            }
          }
        }
      }
    },
    "/api/migration/dataset": {
      "get": {
        "summary": "Api Migration",
        "operationId": "api_migration_api_migration_dataset_get",
        "responses": {
          "200": {
            "description": "Successful Response",
            "content": {
              "application/json": {
                "schema": {}
              }
            }
          }
        }
      }
    },
    "/api/crunch/data-driven": {
      "get": {
        "summary": "Api Crunch Comparison",
        "operationId": "api_crunch_comparison_api_crunch_data_driven_get",
        "responses": {
          "200": {
            "description": "Successful Response",
            "content": {
              "application/json": {
                "schema": {}
              }
            }
          }
        }
      }
    }
  },
  "components": {
    "schemas": {
      "CopilotRunRequest": {
        "properties": {
          "csv_content": {
            "type": "string",
            "title": "Csv Content"
          },
          "plan_text": {
            "type": "string",
            "title": "Plan Text",
            "default": ""
          },
          "spot_price_frontier": {
            "type": "number",
            "title": "Spot Price Frontier",
            "default": 5.0
          },
          "spot_price_discounted": {
            "type": "number",
            "title": "Spot Price Discounted",
            "default": 3.63
          },
          "horizon_days": {
            "type": "integer",
            "title": "Horizon Days",
            "default": 90
          },
          "num_scenarios": {
            "type": "integer",
            "title": "Num Scenarios",
            "default": 3000
          },
          "prompts": {
            "anyOf": [
              {
                "items": {
                  "type": "string"
                },
                "type": "array"
              },
              {
                "type": "null"
              }
            ],
            "title": "Prompts"
          }
        },
        "type": "object",
        "required": [
          "csv_content"
        ],
        "title": "CopilotRunRequest"
      },
      "FitCheckRequest": {
        "properties": {
          "prompts": {
            "items": {
              "type": "string"
            },
            "type": "array",
            "title": "Prompts"
          },
          "spot_price_frontier": {
            "type": "number",
            "title": "Spot Price Frontier",
            "default": 5.0
          },
          "spot_price_discounted": {
            "type": "number",
            "title": "Spot Price Discounted",
            "default": 3.63
          }
        },
        "type": "object",
        "required": [
          "prompts"
        ],
        "title": "FitCheckRequest"
      },
      "HTTPValidationError": {
        "properties": {
          "detail": {
            "items": {
              "$ref": "#/components/schemas/ValidationError"
            },
            "type": "array",
            "title": "Detail"
          }
        },
        "type": "object",
        "title": "HTTPValidationError"
      },
      "ParseRequest": {
        "properties": {
          "csv_content": {
            "type": "string",
            "title": "Csv Content"
          }
        },
        "type": "object",
        "required": [
          "csv_content"
        ],
        "title": "ParseRequest"
      },
      "ValidationError": {
        "properties": {
          "loc": {
            "items": {
              "anyOf": [
                {
                  "type": "string"
                },
                {
                  "type": "integer"
                }
              ]
            },
            "type": "array",
            "title": "Location"
          },
          "msg": {
            "type": "string",
            "title": "Message"
          },
          "type": {
            "type": "string",
            "title": "Error Type"
          },
          "input": {
            "title": "Input"
          },
          "ctx": {
            "type": "object",
            "title": "Context"
          }
        },
        "type": "object",
        "required": [
          "loc",
          "msg",
          "type"
        ],
        "title": "ValidationError"
      }
    }
  }
}
```
