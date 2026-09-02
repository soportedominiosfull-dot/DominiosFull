CREATE DATABASE  IF NOT EXISTS `dominios_full` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci */ /*!80016 DEFAULT ENCRYPTION='N' */;
USE `dominios_full`;
-- MySQL dump 10.13  Distrib 8.0.43, for Win64 (x86_64)
--
-- Host: localhost    Database: dominios_full
-- ------------------------------------------------------
-- Server version	8.0.43

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `compras`
--

DROP TABLE IF EXISTS `compras`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `compras` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int DEFAULT NULL,
  `producto` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `precio` decimal(10,2) DEFAULT NULL,
  `fecha` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `factura_enviada` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT 'no',
  `metodo_pago` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT 'Pasarela de Pago Online',
  `factura_id` int DEFAULT NULL,
  `fecha_vencimiento` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  KEY `factura_id` (`factura_id`),
  CONSTRAINT `compras_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `usuarios` (`id`),
  CONSTRAINT `compras_ibfk_2` FOREIGN KEY (`factura_id`) REFERENCES `facturas` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `compras`
--

LOCK TABLES `compras` WRITE;
/*!40000 ALTER TABLE `compras` DISABLE KEYS */;
INSERT INTO `compras` VALUES (1,4,'.com',65000.00,'2026-08-27 20:47:30','no','Pasarela de Pago Online',1,NULL),(2,4,'Jupiter 10 Gigas',125000.00,'2026-08-27 21:05:06','no','Pasarela de Pago Online',2,NULL),(3,4,'VPS Enterprise',149900.00,'2026-08-27 20:46:31','no','Pasarela de Pago Online',NULL,NULL);
/*!40000 ALTER TABLE `compras` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `facturas`
--

DROP TABLE IF EXISTS `facturas`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `facturas` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `fecha_emision` datetime DEFAULT CURRENT_TIMESTAMP,
  `total` decimal(10,2) NOT NULL,
  `estado` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT 'pendiente',
  `concepto` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT 'Servicio Web',
  `fecha_vencimiento` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `facturas_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `usuarios` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `facturas`
--

LOCK TABLES `facturas` WRITE;
/*!40000 ALTER TABLE `facturas` DISABLE KEYS */;
INSERT INTO `facturas` VALUES (1,4,'2026-08-27 15:47:30',65000.00,'Pendiente','Renovación Anual - .com','2026-09-26 15:47:30'),(2,4,'2026-08-27 16:05:06',125000.00,'Pagada','Renovación Anual - Jupiter 10 Gigas','2026-09-26 16:05:06');
/*!40000 ALTER TABLE `facturas` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `productos`
--

DROP TABLE IF EXISTS `productos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `productos` (
  `id_productos` int NOT NULL,
  `nombre` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `precio` int NOT NULL,
  `categoria` enum('dominio','hosting','vps') CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `destacado` tinyint(1) DEFAULT '0',
  `precio_oferta` decimal(10,2) DEFAULT NULL,
  `oferta_fin` datetime DEFAULT NULL,
  PRIMARY KEY (`id_productos`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `productos`
--

LOCK TABLES `productos` WRITE;
/*!40000 ALTER TABLE `productos` DISABLE KEYS */;
INSERT INTO `productos` VALUES (1,'.com',65000,'dominio',1,NULL,NULL),(2,'.net',69900,'dominio',1,NULL,NULL),(3,'.info',56900,'dominio',1,NULL,NULL),(4,'.org',69900,'dominio',1,NULL,NULL),(5,'.biz',36000,'dominio',1,NULL,NULL),(6,'.us',39900,'dominio',1,NULL,NULL),(7,'.mobi',49900,'dominio',1,NULL,NULL),(8,'.eu',65000,'dominio',1,NULL,NULL),(9,'.com.co',65000,'dominio',0,NULL,NULL),(10,'.co',65000,'dominio',0,NULL,NULL),(11,'.name',79000,'dominio',0,NULL,NULL),(12,'.in',56900,'dominio',0,NULL,NULL),(13,'.tv',169900,'dominio',0,NULL,NULL),(14,'.ws',135900,'dominio',0,NULL,NULL),(15,'.es',123000,'dominio',0,NULL,NULL),(16,'.net.co',56900,'dominio',0,NULL,NULL),(17,'.eu.com',145000,'dominio',0,NULL,NULL),(18,'.us.com',145000,'dominio',0,NULL,NULL),(19,'.life',189000,'dominio',0,NULL,NULL),(20,'.tel',57900,'dominio',0,NULL,NULL),(21,'Tierra 2 Gigas',35000,'hosting',0,NULL,NULL),(22,'Neptuno 4 Gigas',50000,'hosting',0,NULL,NULL),(23,'Urano 6 Gigas',85000,'hosting',0,NULL,NULL),(24,'Saturno 8 Gigas',99000,'hosting',0,NULL,NULL),(25,'Jupiter 10 Gigas',125000,'hosting',0,NULL,NULL),(26,'PYMES PLUS 20 GB',250000,'hosting',0,NULL,NULL),(31,'VPS Starter',39900,'vps',0,NULL,NULL),(32,'VPS Pro',79900,'vps',1,NULL,NULL),(33,'VPS Enterprise',149900,'vps',0,NULL,NULL);
/*!40000 ALTER TABLE `productos` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `resenas`
--

DROP TABLE IF EXISTS `resenas`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `resenas` (
  `id_resena` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `comentario` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci,
  `estrellas` int NOT NULL,
  `fecha` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id_resena`),
  KEY `fk_resenas_usuarios` (`user_id`),
  CONSTRAINT `fk_resenas_usuarios` FOREIGN KEY (`user_id`) REFERENCES `usuarios` (`id`) ON DELETE CASCADE,
  CONSTRAINT `resenas_chk_1` CHECK ((`estrellas` between 1 and 5))
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `resenas`
--

LOCK TABLES `resenas` WRITE;
/*!40000 ALTER TABLE `resenas` DISABLE KEYS */;
INSERT INTO `resenas` VALUES (1,4,'Excelente servicio, servidores veloces y sin caídas, 100% recomendado ?',5,'2026-08-27 15:45:34'),(2,4,'wsad',5,'2026-09-01 15:41:18'),(3,4,'ddd',5,'2026-09-01 15:41:21'),(4,4,'matias en un ñoño :V',1,'2026-09-01 15:42:17');
/*!40000 ALTER TABLE `resenas` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `usuarios`
--

DROP TABLE IF EXISTS `usuarios`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `usuarios` (
  `id` int NOT NULL AUTO_INCREMENT,
  `nombre` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `email` varchar(150) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `contraseña` varchar(260) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `fecha_registro` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `rol` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT 'cliente',
  `ultimo_login` datetime DEFAULT NULL,
  `estado` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT 'activo',
  `codigo_2fa` varchar(6) COLLATE utf8mb4_general_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `usuarios`
--

LOCK TABLES `usuarios` WRITE;
/*!40000 ALTER TABLE `usuarios` DISABLE KEYS */;
INSERT INTO `usuarios` VALUES (1,'Samuel Chacón','samuel_chaconst@gfc.edu.co','scrypt:32768:8:1$I3wlLrDqAiQyadSW$c1d8fa4848c4ba4db550d6777548fa1e33d7f85728f7111c7913d6591bb46905284a091889608faeaaa70f92a9427a9d2a47440928d74f65bb99e7b740645695','2026-03-26 20:51:02','superadmin','2026-09-01 16:36:20','activo',NULL),(2,'Camilo','andres_pacasirasanchezst@gfc.edu.co','scrypt:32768:8:1$MlHeF2i87A9XGv8e$a170e58c9fdedc50a9ba63f926b1dc191015d5e66123cf623371a9c1e82c570330cab560a7c898359aa6bfd5e3d40d8c585383bae6b749931ca51ae50ca0f35e','2026-03-26 20:52:38','superadmin','2026-09-01 16:27:55','activo',NULL),(3,'Daniel Matias','danielmatiassalcedosalcedo@gmail.com','scrypt:32768:8:1$9hrrtTz5aKqDW5NO$9dc3d9e9ace003bcea813f818d178e62afb9d382181e3e5c21c4ac2653ce46378300fa38f1d730c89d4675077cea188c4f3ec7612c6a042f682d8571852843e2','2026-03-26 21:01:23','admin','2026-08-28 08:28:24','activo',NULL),(4,'Test','test.dominiosfull@gmail.com','scrypt:32768:8:1$6pY14ddE9A70Knx6$a4da8681c0c47ffaa1b010caea5261490bee8ab62699ce46f37ff2407e1b218994428bee15b99ee30cf84bcc78f4e9b9d2d28f4b6c75111d4d2ef6fee1e99cf4','2026-08-27 20:43:46','cliente','2026-09-01 16:29:02','activo',NULL),(5,'Nicolas','nicolas_cardenascruzst@gfc.edu.co','scrypt:32768:8:1$ZtAAHejav7ktXKQi$4ee0c8aff5424df50aac2fadd98ac4c893c1659ab6fcd6898a86de548092e6366ee8c2ab51e819ebd0c112055fd9d70354609cf42367b1c9b0255caf8de5a939','2026-08-28 14:01:45','admin','2026-08-31 11:10:27','activo',NULL);
/*!40000 ALTER TABLE `usuarios` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping events for database 'dominios_full'
--

--
-- Dumping routines for database 'dominios_full'
--
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-09-02 12:32:22
