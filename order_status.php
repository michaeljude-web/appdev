<?php
header('Content-Type: application/json');
$host = 'localhost'; $user = 'root'; $password = ''; $database = 'app';
$conn = new mysqli($host, $user, $password, $database);

$code = isset($_GET['code']) ? $_GET['code'] : '';
if (!$code) { echo json_encode(['error' => 'no code']); exit; }

$stmt = $conn->prepare("SELECT id, status FROM orders WHERE order_code = ?");
$stmt->bind_param("s", $code);
$stmt->execute();
$row = $stmt->get_result()->fetch_assoc();

if (!$row) { echo json_encode(['error' => 'not found']); exit; }

$stmt2 = $conn->prepare("SELECT COUNT(*) AS pos FROM orders WHERE status IN ('pending','waiting') AND id <= ?");
$stmt2->bind_param("i", $row['id']);
$stmt2->execute();
$pos_row = $stmt2->get_result()->fetch_assoc();

echo json_encode([
    'code'     => $code,
    'status'   => $row['status'],
    'position' => (int)$pos_row['pos']
]);
$conn->close();