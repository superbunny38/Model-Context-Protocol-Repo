#!/usr/bin/env node

import { authenticate } from "@google-cloud/local-auth";
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListResourcesRequestSchema,
  ListToolsRequestSchema,
  ReadResourceRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import fs from "fs";
import { google } from "googleapis";
import path from "path";
import { fileURLToPath } from 'url';
import { Readable } from "stream";

const drive = google.drive("v3");

const server = new Server(
  {
    name: "example-servers/gdrive",
    version: "0.1.0",
  },
  {
    capabilities: {
      resources: {},
      tools: {},
    },
  },
);

server.setRequestHandler(ListResourcesRequestSchema, async (request) => {
  const pageSize = 10;
  const params: any = {
    pageSize,
    fields: "nextPageToken, files(id, name, mimeType)",
  };

  if (request.params?.cursor) {
    params.pageToken = request.params.cursor;
  }

  const res = await drive.files.list(params);
  const files = res.data.files!;

  return {
    resources: files.map((file) => ({
      uri: `gdrive:///${file.id}`,
      mimeType: file.mimeType,
      name: file.name,
    })),
    nextCursor: res.data.nextPageToken,
  };
});

server.setRequestHandler(ReadResourceRequestSchema, async (request) => {
  const fileId = request.params.uri.replace("gdrive:///", "");

  // First get file metadata to check mime type
  const file = await drive.files.get({
    fileId,
    fields: "mimeType",
  });

  // For Google Docs/Sheets/etc we need to export
  if (file.data.mimeType?.startsWith("application/vnd.google-apps")) {
    let exportMimeType: string;
    switch (file.data.mimeType) {
      case "application/vnd.google-apps.document":
        exportMimeType = "text/markdown";
        break;
      case "application/vnd.google-apps.spreadsheet":
        exportMimeType = "text/csv";
        break;
      case "application/vnd.google-apps.presentation":
        exportMimeType = "text/plain";
        break;
      case "application/vnd.google-apps.drawing":
        exportMimeType = "image/png";
        break;
      default:
        exportMimeType = "text/plain";
    }

    const res = await drive.files.export(
      { fileId, mimeType: exportMimeType },
      { responseType: "text" },
    );

    return {
      contents: [
        {
          uri: request.params.uri,
          mimeType: exportMimeType,
          text: res.data,
        },
      ],
    };
  }

  // For regular files download content
  const res = await drive.files.get(
    { fileId, alt: "media" },
    { responseType: "arraybuffer" },
  );
  const mimeType = file.data.mimeType || "application/octet-stream";
  if (mimeType.startsWith("text/") || mimeType === "application/json") {
    return {
      contents: [
        {
          uri: request.params.uri,
          mimeType: mimeType,
          text: Buffer.from(res.data as ArrayBuffer).toString("utf-8"),
        },
      ],
    };
  } else {
    return {
      contents: [
        {
          uri: request.params.uri,
          mimeType: mimeType,
          blob: Buffer.from(res.data as ArrayBuffer).toString("base64"),
        },
      ],
    };
  }
});

server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: "search",
        description: "Search for files in Google Drive",
        inputSchema: {
          type: "object",
          properties: {
            query: {
              type: "string",
              description: "Search query",
            },
          },
          required: ["query"],
        },
      },
      {
        name: "read",
        description: "Read the contents of a file from Google Drive using its fileId",
        inputSchema: {
          type: "object",
          properties: {
            fileId: {
              type: "string",
              description: "The ID of the file to read",
            },
          },
          required: ["fileId"],
        },
      },
      {
        name: "create",
        description: "Create a new file in Google Drive",
        inputSchema: {
          type: "object",
          properties: {
            name: {
              type: "string",
              description: "The name of the file to create",
            },
            mimeType: {
              type: "string",
              description: "The MIME type of the file (e.g., text/plain, application/json)",
            },
            content: {
              type: "string",
              description: "The content of the file",
            },
          },
          required: ["name", "mimeType", "content"],
        },
      },
      {
        name: "edit",
        description: "Edit the content of an existing file in Google Drive",
        inputSchema: {
          type: "object",
          properties: {
            fileId: {
              type: "string",
              description: "The ID of the file to edit",
            },
            content: {
              type: "string",
              description: "The new content of the file",
            },
          },
          required: ["fileId", "content"],
        },
      },
      {
        name: "delete",
        description: "Delete a file from Google Drive using its fileId",
        inputSchema: {
          type: "object",
          properties: {
            fileId: {
              type: "string",
              description: "The ID of the file to delete",
            },
          },
          required: ["fileId"],
        },
      },
      {
        name: "move",
        description: "Move a file to a different folder in Google Drive",
        inputSchema: {
          type: "object",
          properties: {
            fileId: {
              type: "string",
              description: "The ID of the file to move",
            },
            targetFolderId: {
              type: "string",
              description: "The ID of the target folder",
            },
          },
          required: ["fileId", "targetFolderId"],
        },
      },
    ],
  };
});

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  if (request.params.name === "search") {
    const userQuery = request.params.arguments?.query as string;
    const escapedQuery = userQuery.replace(/\\/g, "\\\\").replace(/'/g, "\\'");
    const formattedQuery = `fullText contains '${escapedQuery}'`;

    const res = await drive.files.list({
      q: formattedQuery,
      pageSize: 10,
      fields: "files(id, name, mimeType, modifiedTime, size)",
    });

    const fileList = res.data.files?.map((file: any) => ({
      name: file.name,
      mimeType: file.mimeType,
      fileId: file.id,
    }));

    return {
      content: [
        {
          type: "text",
          text: `Found ${res.data.files?.length ?? 0} files:\n${fileList
            ?.map((file) => `${file.name} (${file.mimeType}) [ID: ${file.fileId}]`)
            .join("\n")}`,
        },
      ],
      isError: false,
    };
  } else if (request.params.name === "read") {
    const fileId = request.params.arguments?.fileId as string;

    // Fetch file metadata to determine its MIME type
    const file = await drive.files.get({
      fileId,
      fields: "mimeType",
    });

    // Handle Google Docs/Sheets/etc by exporting their content
    if (file.data.mimeType?.startsWith("application/vnd.google-apps")) {
      let exportMimeType: string;
      switch (file.data.mimeType) {
        case "application/vnd.google-apps.document":
          exportMimeType = "text/markdown";
          break;
        case "application/vnd.google-apps.spreadsheet":
          exportMimeType = "text/csv";
          break;
        case "application/vnd.google-apps.presentation":
          exportMimeType = "text/plain";
          break;
        case "application/vnd.google-apps.drawing":
          exportMimeType = "image/png";
          break;
        default:
          exportMimeType = "text/plain";
      }

      const res = await drive.files.export(
        { fileId, mimeType: exportMimeType },
        { responseType: "text" },
      );

      return {
        content: [
          {
            type: "text",
            text: res.data,
          },
        ],
        isError: false,
      };
    }

    // Handle regular files by downloading their content
    const res = await drive.files.get(
      { fileId, alt: "media" },
      { responseType: "arraybuffer" },
    );
    const mimeType = file.data.mimeType || "application/octet-stream";
    if (mimeType.startsWith("text/") || mimeType === "application/json") {
      return {
        content: [
          {
            type: "text",
            text: Buffer.from(res.data as ArrayBuffer).toString("utf-8"),
          },
        ],
        isError: false,
      };
    } else {
      return {
        content: [
          {
            type: "blob",
            blob: Buffer.from(res.data as ArrayBuffer).toString("base64"),
            mimeType,
          },
        ],
        isError: false,
      };
    }
  } else if (request.params.name === "create") {
    const { name, mimeType, content } = request.params.arguments as {
      name: string;
      mimeType: string;
      content: string;
    };

    const fileMetadata = {
      name,
      mimeType,
    };

    const media = {
      mimeType,
      body: Readable.from(content),
    };

    const res = await drive.files.create({
      requestBody: fileMetadata,
      media,
      fields: "id, name, mimeType",
    });

    return {
      content: [
        {
          type: "text",
          text: `File created successfully: ${res.data.name} (ID: ${res.data.id}, MIME type: ${res.data.mimeType})`,
        },
      ],
      isError: false,
    };
  } else if (request.params.name === "edit") {
    const { fileId, content } = request.params.arguments as {
      fileId: string;
      content: string;
    };

    // Update the file content
    const media = {
      body: Readable.from(content),
    };

    const res = await drive.files.update({
      fileId,
      media,
      fields: "id, name, mimeType",
    });

    return {
      content: [
        {
          type: "text",
          text: `File updated successfully: ${res.data.name} (ID: ${res.data.id}, MIME type: ${res.data.mimeType})`,
        },
      ],
      isError: false,
    };
  } else if (request.params.name === "delete") {
    const { fileId } = request.params.arguments as {
      fileId: string;
    };

    // Move the file to the trash
    const res = await drive.files.update({
      fileId,
      requestBody: {
        trashed: true,
      },
    });

    return {
      content: [
        {
          type: "text",
          text: `File with ID ${fileId} has been moved to the trash.`,
        },
      ],
      isError: false,
    };
  } else if (request.params.name === "move") {
    const { fileId, targetFolderId } = request.params.arguments as {
      fileId: string;
      targetFolderId: string;
    };

    // Retrieve the current parents of the file
    const file = await drive.files.get({
      fileId,
      fields: "parents",
    });

    const previousParents = file.data.parents?.join(",") || "";

    // Move the file to the new folder
    const res = await drive.files.update({
      fileId,
      addParents: targetFolderId,
      removeParents: previousParents,
      fields: "id, name, parents",
    });

    return {
      content: [
        {
          type: "text",
          text: `File moved successfully: ${res.data.name} (ID: ${res.data.id}) to folder ID: ${targetFolderId}`,
        },
      ],
      isError: false,
    };
  }

  throw new Error("Tool not found");
});

const credentialsPath = process.env.GDRIVE_CREDENTIALS_PATH || path.join(
  path.dirname(fileURLToPath(import.meta.url)),
  "../../../.gdrive-server-credentials.json",
);

async function authenticateAndSaveCredentials() {
  console.log("Launching auth flow…");
  const auth = await authenticate({
    keyfilePath: process.env.GDRIVE_OAUTH_PATH || path.join(
      path.dirname(fileURLToPath(import.meta.url)),
      "../../../gcp-oauth.keys.json",
    ),
    scopes: ["https://www.googleapis.com/auth/drive"], // Updated scope for full access
  });
  fs.writeFileSync(credentialsPath, JSON.stringify(auth.credentials));
  console.log("Credentials saved. You can now run the server.");
}

async function loadCredentialsAndRunServer() {
  if (!fs.existsSync(credentialsPath)) {
    console.error(
      "Credentials not found. Please run with 'auth' argument first.",
    );
    process.exit(1);
  }

  const credentials = JSON.parse(fs.readFileSync(credentialsPath, "utf-8"));
  const auth = new google.auth.OAuth2();
  auth.setCredentials(credentials);
  google.options({ auth });

  console.error("Credentials loaded. Starting server.");
  const transport = new StdioServerTransport();
  await server.connect(transport);
}

if (process.argv[2] === "auth") {
  authenticateAndSaveCredentials().catch(console.error);
} else {
  loadCredentialsAndRunServer().catch(console.error);
}
